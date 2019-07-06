""" Use this script to import data into Phamerator database using the
UNIX command line interface so that the import process provides
interactive feedback about the import process.
"""



# Built-in libraries
import time, sys, os, getpass, csv, re, shutil
import json, urllib
from datetime import datetime



# Import third-party modules
try:
    pass
except ModuleNotFoundError as err:
    print(err)
	sys.exit(1)





#TODO replace with new function
#Get the command line parameters
try:
    database = sys.argv[1]
    phageListDir = sys.argv[2]
    updateFile = sys.argv[3]
except:
    print "\n\n\
            This is a python script to import and update phage genomes in the Phamerator database.\n\
            It requires three arguments:\n\
            First argument: name of MySQL database that will be updated (e.g. 'Actino_Draft').\n\
            Second argument: directory path to the folder of genome files that will be uploaded (genbank-formatted).\n\
            Third argument: directory path to the import table file with the following columns (csv-formatted):\n\
                1. Action to implement on the database (add, remove, replace, update)\n\
                2. PhageID to add or update\n\
                3. Host genus of the updated phage\n\
                4. Cluster of the updated phage\n\
                5. Subcluster of the updated phage\n\
                6. Annotation status of the updated phage (draft, final, gbk)\n\
                7. Annotation authorship of the updated phage (hatfull, gbk)\n\
                8. Gene description field of the updated phage (product, note, function)\n\
                9. Accession of the updated phage\n\
                10. Run mode of the updated phage\n\
                11. PhageID that will be removed or replaced\n\n"
	sys.exit(1)











#TODO replace with new functions
#Expand home directory
home_dir = os.path.expanduser('~')


#Verify the genome folder exists

#Add '/' at the end if it's not there
if phageListDir[-1] != "/":
    phageListDir = phageListDir + "/"


#Expand the path if it references the home directory
if phageListDir[0] == "~":
    phageListDir = home_dir + phageListDir[1:]

#Expand the path, to make sure it is a complete directory path (in case user inputted path with './path/to/folder')
phageListDir = os.path.abspath(phageListDir)



if os.path.isdir(phageListDir) == False:
    print "\n\nInvalid input for genome folder.\n\n"
    sys.exit(1)






#Verify the import table path exists
#Expand the path if it references the home directory
if updateFile[0] == "~":
    updateFile = home_dir + updateFile[1:]

#Expand the path, to make sure it is a complete directory path (in case user inputted path with './path/to/folder')
updateFile = os.path.abspath(updateFile)
if os.path.exists(updateFile) == False:
    print "\n\nInvalid input for import table file.\n\n"
    sys.exit(1)











#TODO replace with new function
#Create output directories
date = time.strftime("%Y%m%d")

failed_folder = '%s_failed_upload_files' % date
success_folder = '%s_successful_upload_files' % date

try:
    os.mkdir(os.path.join(phageListDir,failed_folder))
except:
    print "\nUnable to create output folder: %s" % os.path.join(phageListDir,failed_folder)
    sys.exit(1)


try:
    os.mkdir(os.path.join(phageListDir,success_folder))
except:
    print "\nUnable to create output folder: %s" % os.path.join(phageListDir,success_folder)
    sys.exit(1)













### Below - refactored script in progress



import prepare_tickets
from functions import phamerator
from functions import flat_files
from functions import tickets

# TODO command now should include an argument that specifies phage_id_field
# from which phage_id should be assigned as flat files are parsed.


# TODO confirm arguments are structured properly.

# TODO confirm directories and files exist.

# TODO confirm import table file exists.

# TODO create output directories.




# Retrieve import ticket data.
# Data is returned as a list of validated ticket objects.
list_of_tickets, list_of_errors = tickets.prepare_tickets(ticket_filename)


# TODO after parsing from import table:
# 1. set case for all fields.
# 2. confirm all tickets have a valid type.
# 3. populate Genome object.
# 4. retrieve data if needed.
# 5. confirm correct fields are populated based on ticket type.
# 6. check for PhageID conflicts.





# Evaluate the tickets to ensure they are structured properly.

# Each ticket should be complete, now that data from PhagesDB has been
# retrieved. Validate each ticket by checking each field in the ticket
# that it is populated correctly.

# TODO not sure if I should pass a list of valid types to this function.
for ticket in ticket_list:
    evaluate.check_import_ticket_structure(ticket)






# Now that individual tickets have been validated,
# validate the entire group of tickets.

#TODO this should return information
eval_list = tickets.compare_tickets(ticket_list)



# TODO check for ticket errors = exit script if not structured correctly.
# Iterate through tickets and collect all evals.


if len(list_of_errors) > 0:
    sys.exit(1)








# Retrieve data from Phamerator.

# TODO create SQL connector object using parsed arguments.
# TODO it may be better to create the SQL object with the
# prepare_phamerator_data module.


# Retrieve all data from Phamerator
retrieved_phamerator_data = phamerator.retrieve_sql_data(sql_obj)

# Create a dictionary of all data retrieved.
# Key = PhageID.
# Value = Genome object with parsed data.
phamerator_genome_dict = \
    phamerator.create_phamerator_dict(retrieved_phamerator_data)

# Create sets of unique values for different data fields.
phamerator_data_sets = phamerator.create_data_sets(phamerator_genome_dict)


# TODO check for phamerator data errors = exit script if there are errors
# TODO the phamerator main function does not yet return errors.
if len(phamerator_errors) > 0:
    sys.exit(1)




# Parse flat files and create list of genome objects
#TODO insert real function

# Identify valid files in folder.
files_in_folder = basic.identify_files(genome_dir)


# Iterate through the list of files.
# Parse each file into a Genome object.
# Returns lists of Genome objects, Eval objects, parsed files,
# and failed files.
# TODO the phage_id_field can be indicated from a new argument in the command.
genomes, all_results, valid_files, failed_files = \
    flat_files.create_parsed_flat_file_list(files_in_folder, phage_id_field)

# TODO check for flat file parsing errors = exit script if there are errors.
if len(all_results) > 0:
    sys.exit(1)






# Tickets will be matched with other genome data.
# Ticket data will be paired with data from PhameratorDB
# and/or a flat file.
# TODO I may want to POP each ticket off this list as I assign to
# matched genome objects.
list_of_matched_objects = []
for ticket in list_of_tickets:
    matched_data_obj = MatchedGenomes()
    matched_data_obj.ticket = ticket
    list_of_matched_objects.append(matched_data_obj)








# Now that Phamerator data has been retrieved and
# Phamerator genome objects created, match them to ticket data
# TODO can probably change this to match_genomes_to_tickets2 function,
# once I generalize it more.
list_of_match_evals = tickets.match_genomes_to_tickets(list_of_matched_objects,
                                                    all_phamerator_data,
                                                    "phamerator")









# Match tickets to flat file data


# First, determine what the strategy is to match tickets to flat files.
# Flat files can be matched to tickets by either the file name
# (if it serves as the phage id) or the parsed phage name from
# the organism field. This is determined by the run mode.
strategy, strategy_eval = assign_match_strategy(list_of_matched_objects)




# TODO check to confirm that genome objects from parsed flat files do not
# contain any duplicate phage_ids, since that is not gauranteed.


# TODO create dictionary of flat file data based on matching strategy.
# Now that flat file parsing assigns the phage_id using a parameter
# retrieved as a command line argument, this step can be updated so that
# it simply creates a dictionary from the phage_id field,
# just like for Phamerator data.
flat_file_dict = flat_files.create_file_dictionary(all_flat_file_data, strategy)

# This is currently implemented within the tickets.match_genomes_to_tickets2
# function.
list_of_matched_objects, list_of_evals = \
    tickets.match_genomes_to_tickets2(list_of_matched_objects,
                                        flat_file_dict,
                                        "import")





# TODO Now that all data has been matched, split matched objects by ticket type.
# Different types of tickets are evaluated differently.
matched_object_dict = create_matched_object_dict(list_of_matched_objects)

list_of_update_objects = matched_object_dict["update"]
list_of_remove_objects = matched_object_dict["remove"]
list_of_add_replace_objects = matched_object_dict["add_replace"]




# TODO
# After parsing flat file
# Prepare gene_id and gene_name appropriately



# TODO now that the flat file to be imported is parsed and matched to a ticket,
# use the ticket to populate specific genome-level fields such as
# host, cluster, subcluster, etc.
index = 0
while index < len(list_of_add_replace_objects):

    matched_object = list_of_add_replace_objects[index]
    tickets.set_ticket_data(matched_object.genome["import"], matched_object.ticket)

    # Also, pair the genomes that will be directly compared.
    genome_pair = GenomePair.GenomePair()
    genome_pair.genome1 = matched_object.genome["import"]
    genome_pair.genome2 = matched_object.genome["phamerator"]
    matched_object.genome_pairs_dict["import_phamerator"] = genome_pair
    index += 1




# TODO implement better.
# For update tickets, populate a Genome object with the fields that
# need to be updated.

index = 0
while index < len(list_of_update_objects):

    matched_object = list_of_update_objects[index]
    update_genome = Genome.Genome()

    # TODO the set_ticket_data might not populate all fields needed for
    # update tickets.
    tickets.set_ticket_data(matched_object.genome["update"], matched_object.ticket)

    # Also, pair the genomes that will be directly compared.
    genome_pair = GenomePair.GenomePair()
    genome_pair.genome1 = matched_object.genome["update"]
    genome_pair.genome2 = matched_object.genome["phamerator"]
    matched_object.genome_pairs_dict["update_phamerator"] = genome_pair

    index += 1




# Perform all evaluations based on the ticket type.

if len(list_of_update_objects) > 0:
    evaluate.check_update_tickets(list_of_update_objects)

if len(list_of_remove_objects) > 0:
    evaluate.check_remove_tickets(list_of_remove_objects)





# TODO after each add_replace ticket is evaluated,
# should the script re-query the database and re-create the
# sets of PhageIDs, Sequences, etc?
if len(list_of_add_replace_objects) > 0:
    evaluate.check_add_replace_tickets(list_of_add_replace_objects)







# Create all SQL statements

# TODO implement all updates

# TODO implement all removes

# TODO import all scrubbed add_replace data into Phamerator.














### Unused code below.


#Not sure what to do with this:
failed_actions = []
file_tally = 0
script_warnings = 0
script_errors = 0


























#Now that all data has been retrieved, split objects by ticket type
#Create separate lists of ticket based on the indicated action: update, add/replace, remove
#TODO I should pop off each matched_object as I assign to next list.
list_of_update_tickets = []
list_of_remove_tickets = []
list_of_add_replace_tickets = []
list_of_unassigned_tickets = []


for matched_data_obj in matched_data_list:
    ticket_type = matched_data_obj.ticket.type
    if ticket_type == "update":
        list_of_update_tickets.append(matched_data_obj)
    elif ticket_type == "remove":
        list_of_remove_tickets.append(matched_data_obj)
    elif (ticket_type == "add" or ticket_type == "replace"):
        list_of_add_replace_tickets.append(matched_data_obj)

    #TODO error handling
    else:
        write_out(output_file,"\nError: during parsing of actions.")
        table_errors += 1





#TODO Compile all ticket-specific errors and ticket-group errors
# decide how to report errors









###
