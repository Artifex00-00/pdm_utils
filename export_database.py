#!/usr/bin/env python
#Database Export Script
#Travis Mavrich
#University of Pittsburgh
#20160713

#After finishing updating the database, and ready to upload to webfactional...




#Import modules
import time, sys, os, getpass
import MySQLdb as mdb
import subprocess




#Get the command line parameters
try:
    database = sys.argv[1]
    main_dir = sys.argv[2]
    backup_dir = sys.argv[3]
    mysql_query_final_dir = sys.argv[4]
except:    
    print "\n\n\
            This is a python script to export Phamerator databases.\n\
            It requires four arguments:\n\
            First argument: name of MySQL database that will be updated (e.g. 'Actino_Draft').\n\
            Second argument: directory path to the Main folder used to store the new database.\n\
            Third argument: directory path to the Backup folder used to store frozen backup versions.\n\
            Fourth argument: directory path to the folder used to stored gene and genome data queried from the new database.\n"
    sys.exit(1)




#Verify the main folder exists
home_dir = os.path.expanduser('~')

#First, expand the path if it references the home directory
if main_dir[0] == "~":
    main_dir = home_dir + main_dir[1:]

#Second, expand the path, to make sure it is a complete directory path (in case user inputted path with './path/to/folder')
main_dir = os.path.abspath(main_dir)


if main_dir[-1] != "/":
    main_dir = main_dir + "/"

if os.path.isdir(main_dir) == False:
    print "\n\nInvalid main database directory path.\n\n"
    sys.exit(1)



#Verify the backup folder exists

#First, expand the path if it references the home directory
if backup_dir[0] == "~":
    backup_dir = home_dir + backup_dir[1:]

#Second, expand the path, to make sure it is a complete directory path (in case user inputted path with './path/to/folder')
backup_dir = os.path.abspath(backup_dir)



if backup_dir[-1] != "/":
    backup_dir = backup_dir + "/"

if os.path.isdir(backup_dir) == False:
    print "\n\nInvalid backup database directory path.\n\n"
    sys.exit(1)



#Verify the query folder exists

#First, expand the path if it references the home directory
if mysql_query_final_dir[0] == "~":
    mysql_query_final_dir = home_dir + mysql_query_final_dir[1:]

#Second, expand the path, to make sure it is a complete directory path (in case user inputted path with './path/to/folder')
mysql_query_final_dir = os.path.abspath(mysql_query_final_dir)


if mysql_query_final_dir[-1] != "/":
    mysql_query_final_dir = mysql_query_final_dir + "/"

if os.path.isdir(mysql_query_final_dir) == False:
    print "\n\nInvalid mysql query directory path.\n\n"
    sys.exit(1)






#Set up MySQL parameters
mysqlhost = 'localhost'
username = getpass.getpass(prompt='mySQL username:')
password = getpass.getpass(prompt='mySQL password:')


#MySQL has changed the way it outputs queries. By default, query files are stored in the directory below.
#I am unable to figure out how to change this to a custom directory. So now the script outputs queries to files in this default directory, and the files get copied to a custom directory.
mysql_query_default_dir = '/var/lib/mysql-files/'


#Exits MySQL
def mdb_exit(message):
    print "\nError: " + `sys.exc_info()[0]`+ ":" +  `sys.exc_info()[1]` + "at: " + `sys.exc_info()[2]`
    print "\nThe export script did not complete."
    print "\nExiting MySQL."
    cur.execute("ROLLBACK")
    cur.execute("SET autocommit = 1")
    cur.close()
    con.close()
    print "\nExiting export script."
    sys.exit(1)




date = time.strftime("%Y%m%d")




#Verify connection to database
try:
    con = mdb.connect(mysqlhost, username, password, database)
    con.autocommit(False)
    cur = con.cursor()
except:
    print "Unsuccessful attempt to connect to the database. Please verify the database, username, and password."
    sys.exit(1)



#Allow user to control whether the database version number is incremented or not.
#This option allows this script to be used to re-export databases, if needed, when no changes to the database have been made (and thus no need to update the version).
version_change = "no"
version_change_valid = False
while version_change_valid == False:
    version_change = raw_input("\nDo you want to increment the database version number? ")

    if (version_change.lower() == "yes" or version_change.lower() == "y"):
        version_change = "yes"
        version_change_valid = True

    elif (version_change.lower() == "no" or version_change.lower() == "n"):                         
        version_change = "no"
        version_change_valid = True

    else:
        print "Invalid response."






#Change database version

try:
    cur.execute("START TRANSACTION")
    cur.execute("SELECT version FROM version")
    version_old = str(cur.fetchone()[0])
    print "Old database version: " + version_old

    if version_change == "yes":


        version_new_int = int(version_old) + 1
        version_new = str(version_new_int)
        print "New database version: " + version_new
        statement = """UPDATE version SET version = %s;""" % version_new_int
        cur.execute(statement)
        cur.execute("COMMIT")
        print "Database version has been updated."

    else:
        version_new = version_old
        print "Database version will not be updated."        
    
except:
    mdb_exit("\nError retrieving database version.\nNo changes have been made to the database.")



#Create a new version file
try:
    print "Creating version file..."
    versionfile="%s.version" % database
    versionfile_handle = open(main_dir + versionfile,'w')
    command_string = "echo %s" % version_new
    command_list = command_string.split(" ")
    proc = subprocess.check_call(command_list,stdout=versionfile_handle)
    print "Version file has been created."

except:
    mdb_exit("\nError creating version file.")











#Now that the version has been updated, make a copy of the database in the MAIN directory, that will be uploaded to webfactional
print "Dumping new %s database to the Main directory..." % database
dumpfile1 = "%s.sql" % database
dumpfile1_handle = open(main_dir + dumpfile1,'w')
command_string = "mysqldump -u %s -p%s --skip-comments %s" % (username,password,database)
command_list = command_string.split(" ")
proc = subprocess.check_call(command_list,stdout=dumpfile1_handle)



#Also, create a backup of the update database in the BACKUP directory
print "Dumping copy of %s database to the Backup directory..." % database
dumpfile2 = "%s_v%s.sql" % (database,version_new)
dumpfile2_handle = open(backup_dir + dumpfile2,'w')
command_string = "mysqldump -u %s -p%s --skip-comments %s" % (username,password,database)
command_list = command_string.split(" ")
proc = subprocess.check_call(command_list,stdout=dumpfile2_handle)



#Export genome and gene data to file
#Filename formatting: DATE_DATABASE_VERSION_genes/genomes.csv
try:
    print "Exporting genome data..."
    filename1 = "%s_%s_v%s_genomes.csv" % (date,database,version_new)   
    statement1 = """SELECT phage.PhageID, phage.Name, phage.HostStrain, phage.Cluster, phage.status, phage.SequenceLength, phage.Accession, phage.DateLastModified FROM phage INTO OUTFILE '%s/%s' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'""" % (mysql_query_default_dir,filename1)
    cur.execute(statement1)

    command_string = "sudo cp %s/%s %s" % (mysql_query_default_dir,filename1,mysql_query_final_dir)
    command_list = command_string.split(" ")
    proc = subprocess.check_call(command_list)



    print "Exporting gene data..."
    filename2 = "%s_%s_v%s_genes.csv" % (date,database,version_new)
    statement2 = """SELECT phage.PhageID, phage.Name, phage.HostStrain, phage.Cluster, phage.status, gene.GeneID, gene.Name, gene.Orientation, gene.Start, gene.Stop, gene.Notes, pham.name FROM gene JOIN phage on gene.PhageID = phage.PhageID JOIN pham on gene.GeneID = pham.GeneID INTO OUTFILE '%s/%s' FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n'""" % (mysql_query_default_dir,filename2)
    cur.execute(statement2)
    cur.execute("COMMIT")
    cur.close()
    con.autocommit(True)
    command_string = "sudo cp %s/%s %s" % (mysql_query_default_dir,filename2,mysql_query_final_dir)
    command_list = command_string.split(" ")
    proc = subprocess.check_call(command_list)

    print "Genome and gene data exported."
        
except:
    mdb_exit("\nError exporting genome or gene data to file.")

con.close()



#Close script.
print "\n\n\n\nExport script completed."




