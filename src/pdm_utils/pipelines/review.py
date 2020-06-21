"""Pipeline to review discrepant or outdated cds product annotations. """

import argparse
import sys
import textwrap
import time
from pathlib import Path

from sqlalchemy import Column
from sqlalchemy import and_
from sqlalchemy.sql import func

from pdm_utils.functions import annotation
from pdm_utils.functions import basic
from pdm_utils.functions import mysqldb_basic
from pdm_utils.functions import pipelines_basic
from pdm_utils.functions import parsing
from pdm_utils.functions import querying

#-----------------------------------------------------------------------------
#GLOBAL VARIABLES

DEFAULT_FOLDER_NAME = f"{time.strftime('%Y%m%d')}_review"
DEFAULT_FOLDER_PATH = Path.cwd()


REVIEW_HEADER = ["Pham", 
             "Final Call",
             "#Members", 
             "Clusters", 
             "#Functions", 
             "Functional Calls"]
GR_HEADER = ["Gene",
             "Phage",
             "Gene#",
             "Cluster",
             "Subcluster",
             "Functional Call",
             "Translation"]

REVIEW_DATA_COLUMNS = ["gene.GeneID", "phage.Cluster"]
GR_DATA_COLUMNS = ["phage.PhageID", "gene.Name", "phage.Cluster", 
                   "phage.Subcluster", "gene.Notes", "gene.Translation"]

BASE_CONDITIONALS = ("phage.Status = final AND "
                     "phage.AnnotationAuthor = 1 AND "
                     "phage.RetrieveRecord = 1")

#-----------------------------------------------------------------------------
#MAIN FUNCTIONS

def main(unparsed_args_list):
    """Uses parsed args to run the entirety of the review pipeline.

    :param unparsed_args_list: Input a list of command line args.
    :type unparsed_args_list: list[str]
    """
    args = parse_review(unparsed_args_list)

    alchemist = pipelines_basic.build_alchemist(args.database)

    values = pipelines_basic.parse_value_input(args.input)
   
    if not args.all_reports:
        gr_reports = args.gene_reports
        s_report = args.summary_report
        psr_reports = args.pham_summary_reports
    else:
        gr_reports = True
        s_report = True
        psr_reports = True

    execute_review(alchemist, args.folder_path, args.folder_name,
                   review=args.review, values=values,
                   filters=args.filters, groups=args.groups, sort=args.sort,
                   s_report=s_report, gr_reports=gr_reports, 
                   psr_reports=psr_reports, verbose=args.verbose)

def parse_review(unparsed_args_list):
    """Parses review arguments and stores them with an argparse object.

    :param unparsed_args_list: Input a list of command line args.
    :type unparsed_args_list: list[str]
    :returns: ArgParse module parsed args.
    """
    DATABASE_HELP = """
        Name of the MySQL database to export from.
        """
    VERBOSE_HELP = """
        Export option that enables progress print statements.
        """
    FOLDER_PATH_HELP = """
        Export option to change the path
        of the directory where the exported files are stored.
            Follow selection argument with the path to the
            desired directory.
        """
    FOLDER_NAME_HELP = """
        Export option to change the name
        of the directory where the exported files are stored.
            Follow selection argument with the desired name.
        """

    ALL_REPORTS_HELP = """
        Export option to toggle export of all report options.
        """
    GENE_REPORTS_HELP = """
        Export option to toggle export of supplemental information about 
        the genes in the phams selected.
        """
    SUMMARY_REPORT_HELP = """
        Export option to toggle export of supplemental information about
        the profile of the phages selected.
        """
    PHAM_SUMMARY_REPORT_HELP = """
        Export option to toggle export of supplemental information about
        the profile of a pham selected for review.
        """

    REVIEW_HELP = """
        Review option to toggle review of phams.  If enabled,
        phams inputted or auto-generated will not be reviewed
        for inconsistencies.
        """
    IMPORT_FILE_HELP = """
        Selection input option that imports values from a csv file.
            Follow selection argument with path to the
            csv file containing the names of each genome in the first column.
        """
    IMPORT_NAMES_HELP = """
        Selection input option that imports values from cmd line input.
            Follow selection argument with space separated
            names of genomes in the database.
        """
   
    WHERE_HELP = """
        Data filtering option that filters data by the inputted expressions.
            Follow selection argument with formatted filter expression:
                {Table}.{Column}={Value}
        """
    GROUP_BY_HELP = """
        Data selection option that groups data by the inputted columns.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """
    ORDER_BY_HELP = """
        Data selection option that sorts data by the inputted columns.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """
    
    parser = argparse.ArgumentParser()

    parser.add_argument("database", type=str,  help=DATABASE_HELP)
    parser.add_argument("-o", "--folder_name", 
                                    type=str,  help=FOLDER_NAME_HELP)
    parser.add_argument("-p", "--folder_path", 
                                    type=pipelines_basic.convert_dir_path,
                                               help=FOLDER_PATH_HELP)
    parser.add_argument("-v", "--verbose", action="store_true", 
                                               help=VERBOSE_HELP)

    parser.add_argument("-a", "--all_reports", action="store_true",
                                               help=ALL_REPORTS_HELP)
    parser.add_argument("-gr", "--gene_reports", action="store_true",
                                               help=GENE_REPORTS_HELP)
    parser.add_argument("-sr", "--summary_report", action="store_true",
                                               help=SUMMARY_REPORT_HELP)
    parser.add_argument("-psr", "--pham_summary_reports", action="store_true",
                                               help=PHAM_SUMMARY_REPORT_HELP)

    parser.add_argument("-r", "--review", action="store_false",
                                               help=REVIEW_HELP)
    parser.add_argument("-if", "--import_files", dest="input",
                                    type=pipelines_basic.convert_file_path,
                                               help=IMPORT_FILE_HELP)
    parser.add_argument("-in", "--import_names", nargs="*", dest="input",
                                               help=IMPORT_NAMES_HELP)

    parser.add_argument("-f", "--where", nargs="?", dest="filters",
                                               help=WHERE_HELP)
    parser.add_argument("-g", "--group_by", nargs="*", dest="groups",
                                               help=GROUP_BY_HELP)
    parser.add_argument("-s", "--order_by", nargs="*", dest="sort",
                                               help=ORDER_BY_HELP)
    
    
    default_folder_name = DEFAULT_FOLDER_NAME
    default_folder_path = DEFAULT_FOLDER_PATH

    parser.set_defaults(folder_name=default_folder_name,
                        folder_path=default_folder_path,
                        input=[], filters="", groups=[], sort=[],
                        review=True, gene_report=False, summary_report=False,
                        verbose=False)

    parsed_args = parser.parse_args(unparsed_args_list[2:])
    return parsed_args

def execute_review(alchemist, folder_path, folder_name, 
                              review=True, values=[],
                              filters="", groups=[], sort=[], s_report=False, 
                              gr_reports=False, psr_reports=False,
                              verbose=False):
    """Executes the entirety of the pham review pipeline.
    
    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param folder_path: Path to a valid dir for new dir creation.
    :type folder_path: Path
    :param folder_name: A name for the export folder.
    :type folder_name: str
    :param csv_title: Title for an appended csv file prefix.
    :type csv_title: str
    :param review: A boolean to toggle filtering of phams by pham discrepancies.
    :type review: bool
    :param values: List of values to filter database results.
    :type values: list[str]
    :param filters: A list of lists with filter values, grouped by ORs.
    :type filters: list[list[str]]
    :param groups: A list of supported MySQL column names to group by.
    :type groups: list[str]
    :param sort: A list of supported MySQL column names to sort by. 
    :param gr_reports: A boolean to toggle export of additional pham information.
    :type gr_reports: bool
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    """
    db_filter = Filter(alchemist=alchemist)
    db_filter.key = ("gene.PhamID")
 
    if values:
        db_filter.values = values

    if verbose:
        print(f"Identified {len(values)} phams to review...")
           
    if filters != "":
        try:
            db_filter.add(filters)
        except:
            print("Please check your syntax for the conditional string:\n"
                 f"{filters}")
            sys.exit(1)
        finally:
            db_filter.update() 
        
        db_filter.parenthesize()

    db_filter.add(BASE_CONDITIONALS)
    db_filter.update()

    if not db_filter.values:
        print("Current settings produced no database hits.")
        sys.exit(1)

    if review: 
        review_phams(db_filter, verbose=verbose)

    if sort:
        db_filter.sort(sort)

    if verbose:
        print("Creating export folder...")
    export_path = folder_path.joinpath(folder_name)
    export_path = basic.make_new_dir(folder_path, export_path, attempt=50)

    conditionals_map = {}
    pipelines_basic.build_groups_map(db_filter, export_path, conditionals_map, 
                                                       groups=groups,
                                                       verbose=verbose)

    if verbose:
        print("Prepared query and path structure, beginning review export...")
    original_phams = db_filter.values
    total_gr_data = {}
    total_psr_data = {}
    for mapped_path in conditionals_map.keys():
        conditionals = conditionals_map[mapped_path]
        db_filter.values = original_phams
        db_filter.values = db_filter.build_values(where=conditionals)

        review_data = get_review_data(alchemist, db_filter, verbose=verbose) 
        write_report(review_data, mapped_path, REVIEW_HEADER,
                     csv_name=f"ReviewReport",
                     verbose=verbose)

        if s_report:
            summary_data = get_summary_data(alchemist, db_filter)
            write_summary_report(alchemist, summary_data, mapped_path,
                                                    verbose=verbose)

        if gr_reports or psr_reports:
            execute_pham_report_export(alchemist, db_filter, mapped_path, 
                                                gr_reports=gr_reports,
                                                psr_reports=psr_reports,
                                                total_gr_data=total_gr_data,
                                                total_psr_data=total_psr_data,
                                                verbose=verbose)
               
def execute_pham_report_export(alchemist, db_filter, export_path, 
                                        gr_reports=False, total_gr_data={},
                                        psr_reports=False, total_psr_data={},
                                                             verbose=False):
    """Executes export of gene data for a reviewed pham.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param export_path: Path to a valid dir for new file creation.
    :type export_path: Path
    :param total_gr_data: Total data extracted for gene reports.
    :type total_gr_data: dict
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    """
    phams = db_filter.values

    pham_report_path = export_path.joinpath("PhamReports")
    pham_report_path.mkdir()

    for pham in phams:
        pham_path = pham_report_path.joinpath(str(pham))
        pham_path.mkdir()

        db_filter.values = [pham]

        if gr_reports:
            try:
                gr_data = total_gr_data[pham]
            except:
                gr_data = get_gr_data(alchemist, db_filter, verbose=verbose)
                total_gr_data[pham] = gr_data

            write_report(gr_data, pham_path, GR_HEADER,
                         csv_name=f"{pham}_GeneReport",
                         verbose=verbose)
        if psr_reports:
            try:
                psr_data = total_psr_data[pham]
            except:
                psr_data = get_psr_data(alchemist, db_filter, verbose=verbose) 
                total_psr_data[pham] = psr_data

            write_pham_summary_report(psr_data, pham_path, verbose=verbose)

def review_phams(db_filter, verbose=False):
    """Finds and stores phams with discrepant function calls in a Filter.

    """
    notes = db_filter.get_column("gene.Notes")
    
    if verbose:
        print("Reviewing phams...")
    
    reviewed_phams = []
    for index in range(len(db_filter.values)):
        pham = db_filter.values[index]
        if verbose:
            print(f"...Analyzing Pham {pham}...")


        query = querying.build_count(db_filter.graph, notes.distinct(),
                                                    where=(db_filter.key==pham))
        func_count = mysqldb_basic.scalar(db_filter.engine, query)

        if func_count <= 1:
           continue              
        
        if verbose:
            print(f"......Detected discrepencies in Pham {pham}") 
        reviewed_phams.append(pham)

    if verbose:
        print(f"Detected {len(reviewed_phams)} disrepent phams...")

    db_filter.values = reviewed_phams

def write_report(data, export_path, header, csv_name="Report",
                                            verbose=False):
    """Outputs a csv file
    """
    if not export_path.is_dir():
        print("Passed in path is not a directory.")
        sys.exit(1)

    file_path = export_path.joinpath(f"{csv_name}.csv")
    if verbose:
        print(f"Writing {file_path.name} in {export_path.name}...")

    basic.export_data_dict(data, file_path, header, include_headers=True)

def write_summary_report(alchemist, summary_data, export_path, verbose=False): 
    if verbose:
        print(f"Writing SummaryReport.txt in {export_path.name}")

    s_path = export_path.joinpath("SummaryReport.txt")
    s_file = open(s_path, "w")

    version_data = summary_data["version_data"]
    recurring_phages = summary_data["recurring_phages"]
    recent_phages = summary_data["recent_phages"]
    
    s_file.write(f"Phams reviewed on: {time.strftime('%d-%m-%Y')}\n")
    s_file.write(f"Database reviewed: {alchemist.database}\n")
    s_file.write(f"Schema version: {version_data['SchemaVersion']} "
                 f"Database version: {version_data['Version']}\n\n") 
    s_file.write(f"Phams reviewed using the following base conditionals:\n")
    s_file.write(f"    {BASE_CONDITIONALS}\n")

    s_file.write(f"\n\n")
    s_file.write(f"Most occuring phages: {', '.join(recurring_phages)}\n")
    s_file.write(f"Phages recently submitted: {', '.join(recent_phages)}\n")
    s_file.close()

def write_pham_summary_report(psr_data, export_path, verbose=False):
    if verbose:
        print(f"Writing SummaryReport.txt in {export_path.name}")

    s_path = export_path.joinpath("SummaryReport.txt")
    s_file = open(s_path, "w")

    s_file.write(f"Pham reviewed: {export_path.name}\n\n")

    s_file.write(f"Left adjacent phams:\n")
    s_file.write(f"{psr_data['left_phams']}\n")

    s_file.write(f"\n")
    s_file.write(f"Right adjacent phams:\n")
    s_file.write(f"{psr_data['right_phams']}\n")

    s_file.write(f"\n\n")
    s_file.write(f"Conserved Database Domains in pham:\n\n")
    for domain in psr_data["cdd_domains"]:
        s_file.write(f"{domain}\n\n")
#-----------------------------------------------------------------------------
#REVIEW-SPECIFIC HELPER FUNCTIONS

def get_review_data(alchemist, db_filter, verbose=False):
    """
    """
    if verbose:
        print("Retrieving data for phams...")
     
    review_columns = get_review_data_columns(alchemist) 
    row_dicts = db_filter.retrieve(review_columns)

    review_data = []
    for pham in row_dicts.keys():
        if verbose:
            print(f"...Processing data for pham {pham}...")
        row_dict = row_dicts[pham]
        row_dict["Notes"] = annotation.get_count_annotations_in_pham(
                                                            alchemist, pham)

        format_review_data(row_dict, pham)
        review_data.append(row_dict)

    return review_data

def get_summary_data(alchemist, db_filter, verbose=False):
    phams = db_filter.values
    phages_histogram = {}

    phages_data = db_filter.retrieve("phage.PhageID", filter=True)

    db_filter.values = phams
    db_filter.transpose("phage.PhageID", set_values=True)
    db_filter.sort("phage.DateLastModified")

    version_data = mysqldb_basic.get_first_row_data(alchemist.engine, "version")

    summary_data = {}
    summary_data["recent_phages"] = db_filter.values
    summary_data["recurring_phages"] = phages_data
    summary_data["version_data"] = version_data
    
    format_summary_data(summary_data)

    db_filter.values = phams
    db_filter.key = "gene.PhamID"
    return summary_data

def get_gr_data(alchemist, db_filter, verbose=False):  
    pham = db_filter.values[0]
    if verbose:
        print(f"Retrieving genes in pham {pham}...")
    db_filter.transpose("gene.GeneID", set_values=True) 
   
    pg_columns = get_gr_data_columns(alchemist) 
    row_dicts = db_filter.retrieve(pg_columns)

    gr_data = []
    for gene in row_dicts.keys():
        if verbose:
            print(f"...Processing data for gene {gene}...")

        row_dict = row_dicts[gene]

        format_gr_data(row_dict, gene)
        gr_data.append(row_dict)

    db_filter.values = [pham]
    db_filter.key = "gene.PhamID"
    return gr_data 

def get_psr_data(alchemist, db_filter, verbose=False):
    pham = db_filter.values[0]
    adjacent_phams = annotation.get_distinct_adjacent_phams(alchemist, pham)
    psr_data = {}

    psr_data["left_phams"] = adjacent_phams["left"]
    psr_data["right_phams"] = adjacent_phams["right"]

    db_filter.values = [pham] 
    db_filter.transpose("domain.Name", set_values=True)
    cdd_domains = db_filter.retrieve("domain.Description")
    psr_data["cdd_domains"] = cdd_domains

    format_psr_data(psr_data)

    db_filter.values = [pham]
    db_filter.key = "gene.PhamID"
    return psr_data

def format_review_data(row_dict, pham):
    """Function to format function report dictionary keys.
    
    :param row_dict: Data dictionary for a function report.
    :type row_dict: dict
    :param pham: PhamID to append to the function report data dictionary.
    :type pham: int
    """
    row_dict["Pham"] = pham
    row_dict["Final Call"] = ""
    row_dict["#Members"] = len(row_dict.pop("GeneID"))
    row_dict["#Functions"] = len(row_dict["Notes"])
 
    row_dict["Clusters"] = ";".join([str(cluster) \
                                    for cluster in row_dict.pop("Cluster")])

    count_functional_calls = []
    notes = row_dict.pop("Notes")
    for key in notes.keys():
        if key is None or key == "": 
            function = "Hypothetical Protein"
        else: 
            function = key

        count_functional_calls.append(
            "".join([function, f"({str(notes[key])})"]))

    row_dict["Functional Calls"] = ";".join(count_functional_calls)

def format_summary_data(summary_data):
    recent_phages = summary_data["recent_phages"]
    recent_phages.reverse()
    recent_phages = basic.partition_list(recent_phages, 5)[0]
    summary_data["recent_phages"] = recent_phages

    phages_data = summary_data["recurring_phages"]
    phages_histogram = {}
    for pham in phages_data.keys():
        basic.increment_histogram(phages_data[pham]["PhageID"], 
                                  phages_histogram)

    recurring_phages = basic.sort_histogram_keys(phages_histogram)
    recurring_phages = basic.partition_list(recurring_phages, 5)[0]
    for i in range(len(recurring_phages)):
        recurring_phages[i] = "".join([recurring_phages[i], 
                            f"({str(phages_histogram[recurring_phages[i]])})"])
    summary_data["recurring_phages"] = recurring_phages

def format_gr_data(row_dict, gene):
    """Function to format gene report dictionary keys.

    :param row_dict: Data dictionary for a gene report.
    :type row_dict: dict
    :param gene: GeneID to append to the gene report data dictionary.
    :type gene: str
    """
    row_dict["Gene"] = gene
    row_dict["Phage"] = row_dict.pop("PhageID")[0]
    row_dict["Gene#"] = row_dict.pop("Name")[0]
    row_dict["Cluster"] = row_dict["Cluster"][0]
    row_dict["Subcluster"] = row_dict["Subcluster"][0]
    row_dict["Translation"] = row_dict["Translation"][0]

    note = row_dict.pop("Notes")[0]
    if note is None or note == "":
        note = "Hypothetical Protein"

    row_dict["Functional Call"] = note

def format_psr_data(psr_data):
    left_phams_list = psr_data["left_phams"]
    left_phams = ", ".join([str(pham) for pham in left_phams_list])
    left_phams = textwrap.wrap(left_phams, 72)
    left_phams = "\n".join(left_phams)
    left_phams = textwrap.indent(left_phams, "    ")
    psr_data["left_phams"] = left_phams 

    right_phams_list = psr_data["right_phams"]
    right_phams = ", ".join([str(pham) for pham in right_phams_list])
    right_phams = textwrap.wrap(right_phams, 72)
    right_phams = "\n".join(right_phams)
    right_phams = textwrap.indent(right_phams, "    ")
    psr_data["right_phams"] = right_phams

    cdd_domains_data = psr_data["cdd_domains"]
    cdd_domains = []
    for domain in cdd_domains_data.keys():
        description = cdd_domains_data[domain]["Description"][0]
        description = textwrap.wrap(description, 72)
        description = "\n".join(description)
        description = textwrap.indent(description, "    ")
        cdd_domain = "".join([domain, "\n", description])
        cdd_domains.append(cdd_domain)
    psr_data["cdd_domains"] = cdd_domains

def get_review_data_columns(alchemist):
    """Gets labelled columns for pham function data retrieval.
    
    :returns: List of labelled columns for function data retrieval.
    :rtype: list[Column]
    """
    review_columns = []

    for column_name in REVIEW_DATA_COLUMNS:
        review_columns.append(querying.get_column(alchemist.metadata, 
                                                                  column_name))

    return review_columns

def get_gr_data_columns(alchemist):
    """Gets labelled columns for pham gene data retrieval.

    :returns: List of labelled columns for gene data retrieval.
    :rtype: list[Column]
    """
    pg_columns = []

    for column_name in GR_DATA_COLUMNS:
        pg_columns.append(querying.get_column(alchemist.metadata, column_name))

    return pg_columns 


if __name__ == "__main__":
    args = sys.argv
    args.insert(0, "")
    main(args)
