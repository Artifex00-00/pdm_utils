#!/usr/bin/env python
#PYTHON code for executing iterative kClust
#Charles Bowman
#20150126
#Updated 20190114 by Christian Gauthier to fix some SQL statements that didn't comply with mysql-5.7.24

import MySQLdb as mdb
import sys, os, random, colorsys, datetime, getpass
import shutil
import tempfile


class TemporaryDirectory(object):
    # see https://stackoverflow.com/questions/6884991/how-to-delete-dir-created-by-python-tempfile-mkdtemp
    """Context manager for tempfile.mkdtemp() so it's usable with "with" statement."""
    def __enter__(self):
        self.name = tempfile.mkdtemp()
        return self.name

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self.name)


def get_consensus_from_long(pham_list):
	"""
	:param pham_list: dict with keys as pham names, values are lists of [geneid, aa seq] strings
	:return: all things written to c.write above

	Here is how to string together the calls into a single bash command for later parallelization:
    kalign -i <infile> | hhmake -v 0 -i /dev/stdin -o /dev/stdout | hhconsensus -v 0 -i /dev/stdin -o <outfile>

	"""
	all_lines = []
	for pham_no, genes in pham_list.items():
		f = open('/tmp/tempquery_{}.txt'.format(pham_no), 'w')
		for gene in genes:
			f.write(">" + gene[0] + '\n')
			f.write(gene[1].replace('-','M') + '\n')
		f.close()

		#print "Aligning " + str(key)
		bashCom = 'kalign -i /tmp/tempquery_{}.txt | hhmake -v 0 -i /dev/stdin -o /dev/stdout | hhconsensus -v 0 -i /dev/stdin -o /tmp/tempcons.txt'.format(pham_no)
		os.system(bashCom)

		"""
		print "Converting " + str(key)
		bashCom = "hhmake -v 0 -i /tmp/tempout.txt"
		os.system(bashCom)

		#print "Building Consensus " + str(key)
		bashCom = "hhconsensus -v 0 -i /tmp/tempout.hhm -o /tmp/tempcons.txt"
		os.system(bashCom)
		"""
		d = open('/tmp/tempcons.txt', 'r')
		lines = d.read().splitlines()
		d.close()
		all_lines.append(">" + str(pham_no) + '\n')
		all_lines.append(lines[2] + '\n')
	return all_lines


#Get the command line parameters
try:
	database = sys.argv[1]
except:

    print "\n\n\
            This is a python script to create gene phamilies in the Phamerator database.\n\
            It requires one argument(s):\n\
            First argument: name of MySQL database that will be updated (e.g. 'Actino_Draft').\n"
    sys.exit(1)

#GET u/n and pw

username = getpass.getpass(prompt='mySQL username:')
password = getpass.getpass(prompt='mySQL password:')

starttime = datetime.datetime.now()


new_set = set()
pre_phams = {}
pre_colors = {}

#build pre-dictionary
try:
	#Connect
	con = mdb.connect('localhost', username, password, database)
	cur = con.cursor()
	print "Connected to Database - Fetching Phams, GeneIDs, and Translations"
	print "..."

	cur.execute("SELECT a.name, a.GeneID, b.color FROM (SELECT p.name, g.GeneID FROM gene g INNER JOIN pham p ON g.GeneID = p.GeneID) AS a INNER JOIN pham_color AS b ON a.name = b.name ORDER BY a.name ASC")
	tuples = cur.fetchall()

	print `len(tuples)` + " old genes"
	for tuple in tuples:
		name, GeneID, color = tuple
		if name in pre_phams.keys():
			pre_phams[name] = pre_phams[name] | set([GeneID])
		else:
			pre_phams[name] = set([GeneID])
			pre_colors[name] = color

	cur.execute("select geneid from gene where geneid not in (select g.GeneID from gene g inner join pham p on g.geneid = p.geneid)")
	tuples = cur.fetchall()

	print `len(tuples)` + " new genes"

	for tuple in tuples:
		GeneID = tuple[0]
		new_set = new_set | set([GeneID])


except mdb.Error, e:

	print "Error %d: %s" % (e.args[0],e.args[1])
	sys.exit(1)

finally:

    if con:
        con.close()


###kClust Analysis Start
#Get the gene information
try:
	#Connect
	con = mdb.connect('localhost', username, password, database)
	cur = con.cursor()
	print "Connected to Database - Fetching GeneIDs and Translations"

	#Clear previous pham data
	cur.execute("TRUNCATE TABLE pham")
	cur.execute("TRUNCATE TABLE pham_color")
	cur.execute("COMMIT")

	#Get gene data
	cur.execute("SELECT GeneID, translation FROM gene")
	tuples = cur.fetchall()

	print `len(tuples)` + " total genes"

	#Build the query file
	f = open('/tmp/tempquery.txt','w')
	for tuple in tuples:
		f.write(">" + tuple[0] + '\n')
		f.write(tuple[1].replace('-','M') + '\n')

except mdb.Error, e:

	print "Error %d: %s" % (e.args[0],e.args[1])
	sys.exit(1)

finally:

    f.close()

    if con:
        con.close()

#Run the first kClust iteration
bashCom = ("kClust -i /tmp/tempquery.txt -d /tmp/kClust -s 3.53 -c .25")
print "kClust Command: " + bashCom
os.system(bashCom)

#Parse the output
g = open('/tmp/kClust/clusters.dmp', 'r')
clusters = g.read()
clusters = clusters.splitlines()
g.close()

g = open('/tmp/kClust/headers.dmp', 'r')
headers = g.read()
headers = headers.splitlines()
g.close()

phams = {}
geneIDs = {}

#recon to sql
try:
	con = mdb.connect('localhost', username, password, database);
	cur = con.cursor()

    	#build the pham dictionary
	for line in clusters:
		line = line.split()
		phams[line[0]] = line[1]

	phams.pop("#", None)

	#build the header dictionary
	for line in headers:
		line = line.split()
		geneIDs[line[0]] = line[1][1:]

	print `len(phams)` + " 1st iteration genes"

	#f = open("/tmp/phirst_pham_insert_log.txt", "w")

	#do the pham inserts
	for key in phams:
		#print "*****"
		#print "Inserting Gene " + key + " - " + geneIDs[key] + " pham - " + phams[key]
		#print ""
		#f.write(`geneIDs[key]` + "\t" + `phams[key]` + "\n")
		cur.execute("INSERT INTO pham(geneid, name) VALUES (%s, %s)" , (geneIDs[key], phams[key]))
	cur.execute("COMMIT")
	#f.close()

except mdb.Error, e:

    print "Error %d: %s" % (e.args[0],e.args[1])
    sys.exit(1)

finally:

    if con:
        con.close()

#Do the second kClust iteration
try:
	#Get a list of genes with phamily and translational data
	con = mdb.connect('localhost', username, password, database)
	print "Connected to Database - Fetching 1st iteration phamily data"
	cur = con.cursor()
	cur.execute("SELECT p.name, g.GeneID, g.translation FROM gene g INNER JOIN pham p ON g.GeneID = p.GeneID ORDER BY name ASC")
	tuples = cur.fetchall()

except mdb.Error, e:
	print "Error %d: %s" % (e.args[0],e.args[1])
	sys.exit(1)

finally:
	if con:
		con.close()


phams = {}

#Build the phamDictionary
print "Building Phamily Dictionary"
for tuple in tuples:
	if tuple[0] in phams.keys():
		phams[tuple[0]].append([tuple[1], tuple[2]])
	else:
		phams[tuple[0]] = []
		phams[tuple[0]].append([tuple[1], tuple[2]])

#Initialize the final consensus file
c1 = open('/tmp/consensi.txt','w')

#Do alignments, conversion, and consensus extraction for all phams
print "Doing Phamily kalignments"
count = 1
length = len(phams)
long_phams = {}
for key in phams:
	if count % 100 == 0:
		print "Processing pham " + `count` + " out of " + `length`
	count += 1
	if (len(phams[key]) < 2):
		#print "Singleton... " + str(key)
		c1.write(">" + str(key) + '\n')
		c1.write(phams[key][0][1] + '\n')
	else:
		long_phams[key] = phams[key]

c1.close()

consensus_lines = get_consensus_from_long(long_phams)

with open('/tmp/consensi.txt','a') as c1:
	for line in consensus_lines:
		c1.write(line)


#do the second kClust iteration
bashCom = ("kClust -i /tmp/consensi.txt -d /tmp/kClust -s 0 -c .5")
os.system(bashCom)

#load the data into the phamerator

#Load the clusters
g = open('/tmp/kClust/clusters.dmp', 'r')
clusters = g.read()
clusters = clusters.splitlines()
g.close()

#Load the headers
g = open('/tmp/kClust/headers.dmp', 'r')
headers = g.read()
headers = headers.splitlines()
g.close()

#Initialize Dictionaries
phams_penultimate = {}
phams_translator = {}
phams_seconditer = {}
phams_firstiter = {}
phams_count = {}

#recon to sql
con = mdb.connect('localhost', username, password, database);
cur = con.cursor()

#build the new pham dictionary
for line in clusters:
	line = line.split()
	phams_seconditer[line[0]] = line[1]
phams_seconditer.pop("#", None)

for line in headers:
	line = line.split()
	phams_firstiter[line[0]] = line[1][1:]

for key in phams_seconditer:
	phams_translator[phams_firstiter[key]] = phams_seconditer[key]

for tuple in tuples:
	#print tuple[1]
	phams_penultimate[tuple[1]] = phams_translator[str(int(tuple[0]))]
	#count whats in what pham
	if phams_penultimate[tuple[1]] in phams_count:
		phams_count[phams_penultimate[tuple[1]]] += 1
	else:
		phams_count[phams_penultimate[tuple[1]]] = 1


#Building the POST-dictionary
post_phams = {}
#f = open("/tmp/phecond_pham_insert_log.txt", "w")

for key in phams_penultimate:

	name, GeneID = phams_penultimate[key], key

	#f.write(`GeneID` + "\t" + `name` + "\n")

	if name in post_phams.keys():
		post_phams[name] = post_phams[name] | set([GeneID])
	else:
		post_phams[name] = set([GeneID])
#f.close()

#Do Phamily Conservationatory Measures
phams_final = {}
phams_colors = {}

post_phams_temp = post_phams.copy()


#f = open("/tmp/post_cons.txt", "w")
#g = open("/tmp/pre_cons.txt", "w")

outcount = 0
total = len(pre_phams)

#Iterate through old and new phams
for pre_key in pre_phams:

	outcount += 1
	print "Pham Name Conservation Search: " + `outcount` + " / " + `total`

	pre = pre_phams[pre_key]
	#g.write(`pre_key` + `pre` + "\n")

	if (pre_key in phams_final.keys()):
			continue;

	for post_key in post_phams_temp:

		post = post_phams_temp[post_key]

		if pre & post == set():
			continue

		#Case 1 + 5 (Identity and Subtraction)
		if pre == post:
			phams_final[pre_key] = post
			phams_colors[pre_key] = pre_colors[pre_key]
			post_phams.pop(post_key, None)
			#f.write(post_key + `post` + "1 + 5\n")
			#print "1 or 5"
			break

		#Case 2 and 4 (Addition and Join) - PHAM GREW
		elif post - pre != set():

			#Case 2 and 4 (Addition and Join)
			if post & new_set != set():

				#Case 4 - Join with new gene
				if (post - (post & new_set)) - pre != set():
					#print "4"
					#f.write(post_key + `post` + "4\n")
					break

				#Case 2 - Addition with new gene
				phams_final[pre_key] = post
				phams_colors[pre_key] = pre_colors[pre_key]
				post_phams.pop(post_key, None)
				#f.write(post_key + `post` + "2\n")
				#print `pre_key` + `phams_final[pre_key]`
				break

			#Case 4 - Join without new gene
			else:
				#f.write(post_key + `post` + "4\n")
				#print "4"
				break

		#Case 3 - split - PHAM SHRANK, BUT NOT BY REMOVAL
		elif pre - post != set():
			#f.write(post_key + `post` + "3\n")
			#print "3"
			break

phams_final[0] = "placeholder"
highest_pham = max(map(int, phams_final.keys())) + 1
del phams_final[0]
#Reassign data for split or joined phams

#f.close()
#g.close()

#f = open("/tmp/phams_final.txt", "w")

#for key in phams_final:
	#f.write(`key` + `phams_final[key]` + "\n")

#f.close()

#f = open("/tmp/post_phams.txt", "w")

for key in post_phams:

	#f.write(key + `post_phams[key]` + "\n")

	new_key = highest_pham
	highest_pham += 1

	phams_final[new_key] = post_phams[key]

	if phams_count[key] > 1:
		h=s=v=0
		while h <= 0: h = random.random()
		while s < 0.5: s = random.random()
		while v < 0.8: v = random.random()
		rgb = colorsys.hsv_to_rgb(h,s,v)
		rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
		hexrgb = '#%02x%02x%02x' % rgb
		phams_colors[new_key] = hexrgb
	else:
		phams_colors[new_key] = '#FFFFFF'

#f.close()
#Insert Data
try:
	con = mdb.connect('localhost', username, password, database)
	print "Connected to Database - Inserting Data"
	cur = con.cursor()

	cur.execute("TRUNCATE TABLE pham")
	cur.execute("TRUNCATE TABLE pham_color")
	cur.execute("COMMIT")

	f = open("/tmp/phinal_pham_insert_log.txt", "w")

	#do the pham inserts
	for key in phams_final:

		for gene in phams_final[key]:
			#print "*****"
			#print "Inserting Gene " + key + " - " + phams_firstiter[key] + " pham - " + phams[key]
			#print ""

			f.write(`gene` + "\t" + `key` + "\n")

			cur.execute("INSERT INTO pham(geneid, name) VALUES (%s, %s)" , (gene, key))
	cur.execute("COMMIT")

	f.close()

	#do the color inserts
	print "Inserting Colors"
	for key in phams_colors:
		#print "Pham " + key + " - " + colors[key]
		cur.execute("INSERT IGNORE INTO pham_color(name, color) VALUES (%s, %s)" , (key, phams_colors[key]))
	cur.execute("COMMIT")

except mdb.Error, e:

	print "Error %d: %s" % (e.args[0],e.args[1])
	sys.exit(1)

finally:

    if con:
        con.close()

#Do housekeeping on color settings for new phams or orphams
try:
	#Connect
	con = mdb.connect('localhost', username, password, database)
	cur = con.cursor()
	print "Connected to Database - Phetching Phalsely Hued Phams"
	print "...\n"
	#Fixed SQL statement to comply with new MYSQL standard where all items selected that aren't functionally dependent on "group by" must be included in "group by"
	#Error Code: 1055.  Expression #1 of SELECT list is not in GROUP BY clause and contains nonaggregated column 'b.id' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=full_group_by_only
	cur.execute("SELECT * FROM (SELECT b.id, COUNT(GeneID) AS count, a.name, b.color FROM pham AS a INNER JOIN pham_color AS b ON a.name = b.name GROUP BY a.name, b.id) AS c WHERE color = '#FFFFFF' AND count > 1")
	tuples = cur.fetchall()

	print `len(tuples)` + " miscolored phamilies found."
	if len(tuples) > 0:
		print " phixing that phor you..."

	for tuple in tuples:
		pham_id, count, name, color = tuple

		h=s=v=0
		while h <= 0: h = random.random()
		while s < 0.5: s = random.random()
		while v < 0.8: v = random.random()
		rgb = colorsys.hsv_to_rgb(h,s,v)
		rgb = (rgb[0]*255,rgb[1]*255,rgb[2]*255)
		hexrgb = '#%02x%02x%02x' % rgb
		newColor = hexrgb

		cur.execute("UPDATE pham_color SET color = %s WHERE id = %s" , (newColor, pham_id))

except mdb.Error, e:

	print "Error %d: %s" % (e.args[0],e.args[1])
	sys.exit(1)

finally:

    cur.execute("COMMIT")
    if con:
        con.close()

#build miscolored orphams
try:
	#Connect
	con = mdb.connect('localhost', username, password, database)
	cur = con.cursor()
	print "\nConnected to Database - Phetching Phalsely Phlagged Orphams"
	print "...\n"
	#Fixed SQL statement to comply with new MYSQL standard where all items selected that aren't functionally dependent on "group by" must be included in "group by"
	#Error Code: 1055.  Expression #1 of SELECT list is not in GROUP BY clause and contains nonaggregated column 'b.id' which is not functionally dependent on columns in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
	cur.execute("SELECT * FROM (SELECT b.id, COUNT(GeneID) AS count, a.name, b.color FROM pham AS a INNER JOIN pham_color AS b ON a.name = b.name GROUP BY a.name, b.id) AS c WHERE color != '#FFFFFF' AND count = 1")
	tuples = cur.fetchall()

	print `len(tuples)` + " miscolored orphams found."
	if len(tuples) > 0:
		print " phixing that phor you..."

	for tuple in tuples:
		pham_id, count, name, color = tuple
		newColor = "#FFFFFF"

		cur.execute("UPDATE pham_color SET color = %s WHERE id = %s" , (newColor, pham_id))


except mdb.Error, e:

	print "Error %d: %s" % (e.args[0],e.args[1])
	sys.exit(1)

finally:

    cur.execute("COMMIT")
    if con:
        con.close()


endtime = datetime.datetime.now()


print starttime
print endtime
