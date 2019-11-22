"""Pipeline to retrieve GenBank records using accessions stored in PhameratorDB."""

import argparse
import pathlib
import sys
import time
from Bio import SeqIO
from pdm_utils.functions import basic
from pdm_utils.functions import ncbi
from pdm_utils.functions import phamerator
from pdm_utils.classes import mysqlconnectionhandler as mch


# TODO unittest.
def parse_args(unparsed_args_list):
    """Verify the correct arguments are selected for getting GenBank records."""
    RETRIEVE_HELP = ("Pipeline to retrieve GenBank records using accessions"
                     "stored in a MySQL Phamerator database.")
    DATABASE_HELP = "Name of the MySQL database."
    OUTPUT_FOLDER_HELP = ("Path to the directory where records will be stored.")
    parser = argparse.ArgumentParser(description=RETRIEVE_HELP)
    parser.add_argument("database", type=str, help=DATABASE_HELP)
    parser.add_argument("output_folder", type=pathlib.Path,
        help=OUTPUT_FOLDER_HELP)

    # Assumed command line arg structure:
    # python3 -m pdm_utils.run <pipeline> <additional args...>
    # sys.argv:      [0]            [1]         [2...]
    args = parser.parse_args(unparsed_args_list[2:])
    return args



# TODO not tested, but nearly identical function in import_genome.py tested.
def connect_to_db(database):
    """Connect to a MySQL database."""
    sql_handle, msg = phamerator.setup_sql_handle(database)
    if sql_handle is None:
        print(msg)
        sys.exit(1)
    else:
        return sql_handle



# TODO unittest.
def main(unparsed_args_list):
    """Run main get_gb_records pipeline."""
    # Parse command line arguments
    args = parse_args(unparsed_args_list)
    date = time.strftime("%Y%m%d")
    args.output_folder = basic.set_path(args.output_folder, kind="dir",
                                        expect=True)

    working_dir = pathlib.Path(f"{date}_genbank_records")
    working_path = basic.make_new_dir(args.output_folder, working_dir,
                                      attempt=10)

    if working_path is None:
        print(f"Invalid working directory '{working_dir}'")
        sys.exit(1)


    # Create data sets
    print("Retrieving accessions from the phamerator database...")
    sql_handle = connect_to_db(args.database)
    accessions = phamerator.create_accession_set(sql_handle)
    if "" in accessions:
        accessions.remove("")
    if None in accessions:
        accessions.remove(None)

    get_genbank_data(working_path, accessions)


# TODO unittest.
def get_genbank_data(output_folder, accession_set):
    """Retrieve genomes from GenBank."""

    batch_size = 200

    # More setup variables if NCBI updates are desired.  NCBI Bookshelf resource
    # "The E-utilities In-Depth: Parameters, Syntax and More", by Dr. Eric
    # Sayers, recommends that a single request not contain more than about 200
    # UIDS so we will use that as our batch size, and all Entrez requests must
    # include the user's email address and tool name.
    email = input("\nPlease provide email address for NCBI: ")
    ncbi.set_entrez_credentials(
        tool="NCBIRecordRetrievalScript",
        email=email)


    # Use esearch to verify the accessions are valid and efetch to retrieve
    # the record
    # Create batches of accessions
    unique_accession_list = list(accession_set)

    # Add [ACCN] field to each accession number
    appended_accessions = \
        [accession + "[ACCN]" for accession in unique_accession_list]


    # When retrieving in batch sizes, first create the list of values
    # indicating which indices of the unique_accession_list should be used
    # to create each batch.
    # For instace, if there are five accessions, batch size of two produces
    # indices = 0,2,4
    batch_indices = basic.create_indices(unique_accession_list, batch_size)
    print(f"There are {len(unique_accession_list)} GenBank accessions to check.")
    for indices in batch_indices:
        batch_index_start = indices[0]
        batch_index_stop = indices[1]
        print("Checking accessions "
              f"{batch_index_start + 1} to {batch_index_stop}...")
        current_batch_size = batch_index_stop - batch_index_start
        delimiter = " | "
        esearch_term = delimiter.join(appended_accessions[
                                      batch_index_start:batch_index_stop])

        # Use esearch for each accession
        search_record = ncbi.run_esearch(db="nucleotide", term=esearch_term,
                            usehistory="y")
        search_count = int(search_record["Count"])
        search_webenv = search_record["WebEnv"]
        search_query_key = search_record["QueryKey"]
        summary_records = ncbi.get_summaries(db="nucleotide",
                                             query_key=search_query_key,
                                             webenv=search_webenv)

        accessions_to_retrieve = []
        for doc_sum in summary_records:
            doc_sum_accession = doc_sum["Caption"]
            accessions_to_retrieve.append(doc_sum_accession)

        if len(accessions_to_retrieve) > 0:
            output_list = ncbi.get_records(accessions_to_retrieve,
                                           db="nucleotide",
                                           rettype="gb",
                                           retmode="text")
            for retrieved_record in output_list:
                ncbi_filename = (f"{retrieved_record.name}.gb")
                flatfile_path = pathlib.Path(output_folder, ncbi_filename)
                SeqIO.write(retrieved_record, str(flatfile_path), "genbank")

###
