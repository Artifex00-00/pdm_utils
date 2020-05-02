"""Basic functions to interact with MySQL and manage databases."""

import subprocess

from pdm_utils.functions import basic


# TODO remove duplicated function in mysqldb module.
def drop_create_db(engine, database):
    """Creates a new, empty database.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :param database: Name of the database to drop and create.
    :type database: str
    :returns: Indicates if drop/create was successful (0) or failed (1).
    :rtype: int
    """
    # First, test if the database already exists within mysql.
    # If there is, delete it so that a new database is installed.
    databases = get_mysql_dbs(engine)
    if database in databases:
        result = drop_db(engine, database)
    else:
        result = 0
    if result == 0:
        result = create_db(engine, database)
    return result


# TODO remove duplicated function in mysqldb module.
def drop_db(engine, database):
    """Delete a database.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :param database: Name of the database to drop.
    :type database: str
    :returns: Indicates if drop was successful (0) or failed (1).
    :rtype: int
    """
    statement = f"DROP DATABASE {database}"
    try:
        engine.execute(statement)
    except:
        return 1
    else:
        return 0

# TODO remove duplicated function in mysqldb module.
def create_db(engine, database):
    """Create a new, empty database.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :param database: Name of the database to create.
    :type database: str
    :returns: Indicates if create was successful (0) or failed (1).
    :rtype: int
    """
    statement = f"CREATE DATABASE {database}"
    try:
        engine.execute(statement)
    except:
        return 1
    else:
        return 0


# TODO remove duplicated function in mysqldb module.
def copy_db(engine, new_database):
    """Copies a database.

    :param engine:
        SQLAlchemy Engine object able to connect to a MySQL database, which
        contains the name of the database that will be copied into
        the new database.
    :type engine: Engine
    :param new_database: Name of the new copied database.
    :type new_database: str
    :returns: Indicates if copy was successful (0) or failed (1).
    :rtype: int
    """
    if engine.url.database == new_database:
        print("Databases are the same so no copy needed.")
        result = 0
    else:
        dbs = get_mysql_dbs(engine)
        if new_database not in dbs:
            print(f"Unable to copy {engine.url.database} to "
                  f"{new_database} since {new_database} does not exist.")
            result = 1
        else:
            #mysqldump -u root -pPWD database1 | mysql -u root -pPWD database2
            cmd1 = mysqldump_command(engine.url.username,
                                     engine.url.password,
                                     engine.url.database)
            cmd2 = mysql_login_command(engine.url.username,
                                       engine.url.password,
                                       new_database)
            print("Copying database...")
            try:
                pipe_commands(cmd1, cmd2)
            except:
                print(f"Unable to copy {engine.url.database} to "
                      f"{new_database} in MySQL due to copying error.")
                result = 1
            else:
                print("Copy complete.")
                result = 0

    return result

# TODO test.
def pipe_commands(command1, command2):
    """Pipe one command into the other."""
    # Per subprocess documentation:
    # 1. For pipes, use Popen instead of check_call.
    # 2. Call p1.stdout.close() to allow p1 to receive a SIGPIPE
    #    if p2 exits, which is called when used as a context manager.
    # communicate() waits for the process to complete.
    with subprocess.Popen(command1, stdout=subprocess.PIPE) as p1:
        with subprocess.Popen(command2, stdin=p1.stdout) as p2:
            p2.communicate()

def mysqldump_command(username, password, database):
    """Construct list of strings representing a mysqldump command."""
    # mysqldump -u root -pPWD database1 > database.sql
    # output filename is not needed since redirecting stdout.
    cmd = f"mysqldump -u {username} -p{password} {database}"
    cmd_list = cmd.split(" ")
    return cmd_list

def mysql_login_command(username, password, database):
    """Construct list of strings representing a mysql command."""
    # mysql -u root -pPWD database
    cmd = (f"mysql -u {username} -p{password} {database}")
    cmd_list = cmd.split(" ")
    return cmd_list

# TODO remove duplicated function in mysqldb module.
def install_db(engine, schema_filepath):
    """Install a MySQL file into the indicated database.

    :param engine:
        SQLAlchemy Engine object able to connect to a MySQL databas.
    :type engine: Engine
    :param schema_filepath: Path to the MySQL database file.
    :type schema_filepath: Path
    :returns: Indicates if copy was successful (0) or failed (1).
    :rtype: int
    """
    cmd = mysql_login_command(engine.url.username,
                              engine.url.password,
                              engine.url.database)
    with schema_filepath.open("r") as fh:
        print("Installing database...")
        try:
            subprocess.check_call(cmd, stdin=fh)
        except:
            print(f"Unable to install {schema_filepath.name} in MySQL.")
            result = 1
        else:
            print("Installation complete.")
            result = 0
    return result





# TODO remove duplicated function in mysqldb module.
# TODO probably move to AlchemyHandler or other module.
# TODO unittest.
def get_mysql_dbs(engine):
    """Retrieve database names from MySQL.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :returns: Set of database names.
    :rtype: set
    """
    query = "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA"
    databases = query_set(engine, query)
    return databases

# TODO remove duplicated function in mysqldb module.
# TODO move tests if available.
def query_set(engine, query):
    """Retrieve set of data from MySQL query.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :param query: MySQL query statement.
    :type query: str
    :returns: Set of queried data.
    :rtype: set
    """
    result_list = engine.execute(query).fetchall()
    set_of_data = basic.get_values_from_tuple_list(result_list)
    return set_of_data





# TODO remove duplicated function in mysqldb module.
# TODO unittest.
def query_dict_list(engine, query):
    """Get the results of a MySQL query as a list of dictionaries.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :param query: MySQL query statement.
    :type query: str
    :returns:
        List of dictionaries, where each dictionary represents a row of data.
    :rtype: list
    """
    result_list = engine.execute(query).fetchall()
    result_dict_list = []
    for row in result_list:
        row_as_dict = dict(row)
        result_dict_list.append(row_as_dict)
    return result_dict_list

# TODO this can be abstracted to convert phage_id_list to primary_key_list.
# TODO remove duplicated function in mysqldb module.
# TODO move tests if available.
def retrieve_data(engine, column=None, query=None, phage_id_list=None):
    """Retrieve genome data from a MySQL database for a single genome.

    The query is modified to include one or more PhageIDs

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :param query:
        A MySQL query that selects valid, specific columns
        from the a valid table without conditioning on a PhageID
        (e.g. 'SELECT PhageID, Cluster FROM phage').
    :type query: str
    :param column:
        A valid column in the table upon which the query can be conditioned.
    :type column: str
    :param phage_id_list:
        A list of valid PhageIDs upon which the query can be conditioned.
        In conjunction with the 'column' parameter, the 'query' is
        modified (e.g. "WHERE PhageID IN ('L5', 'Trixie')").
    :type phage_id_list: list
    :returns:
        A list of items, where each item is a dictionary of
        SQL data for each PhageID.
    :rtype: list
    """
    if (phage_id_list is not None and len(phage_id_list) > 0):
        query = query \
                + f" WHERE {column} IN ('" \
                + "','".join(phage_id_list) \
                + "')"
    query = query + ";"
    result_dict_list = query_dict_list(engine, query)
    return result_dict_list



# TODO remove duplicated function in mysqldb module.
# TODO move tests if available.
def get_distinct_data(engine, table, column, null=None):
    """Get set of distinct values currently in a MySQL database.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :param table: A valid table in the database.
    :type table: str
    :param column: A valid column in the table.
    :type column: str
    :param null: Replacement value for NULL data.
    :type null: misc
    :returns: A set of distinct values from the database.
    :rtype: set
    """
    query = f"SELECT DISTINCT({column}) FROM {table}"
    result_set = query_set(engine, query)

    if None in result_set:
        result_set.remove(None)
        result_set.add(null)

    return result_set


# TODO remove duplicated function in mysqldb module.
# TODO unittest.
def get_db_tables(engine, database):
    """Retrieve tables names from the database.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :returns: Set of table names.
    :rtype: set
    """
    query = ("SELECT table_name FROM information_schema.tables "
             f"WHERE table_schema = '{database}'")
    db_tables = query_set(engine, query)
    return db_tables



# TODO remove duplicated function in mysqldb module.
# TODO unittest.
def get_table_columns(engine, database, table_name):
    """Retrieve columns names from a table.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :param database: Name of the database to query.
    :type database: str
    :param table_name: Name of the table to query.
    :type table_name: str
    :returns: Set of column names.
    :rtype: set
    """
    query = ("SELECT column_name FROM information_schema.columns WHERE "
              f"table_schema = '{database}' AND "
              f"table_name = '{table_name}'")
    columns = query_set(engine, query)
    return columns


# TODO can be used to replace calls to mysqldb.get_phage_table_count()
# TODO remove duplicated function in mysqldb module.
# TODO move tests if available.
def get_table_count(engine, table):
    """Get the current number of genomes in the database.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :returns: Number of rows from the phage table.
    :rtype: int
    """
    query = f"SELECT COUNT(*) FROM {table}"
    result_list = engine.execute(query).fetchall()
    count = result_list[0][0]
    return count




# TODO remove duplicated function in mysqldb module.
# TODO originally coded in export pipeline, so ensure that function is removed.
# TODO unittest.
def get_version_table_data(engine):
    """Retrieves data from the version table.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :returns: Dictionary containing keys "Version" and "SchemaVersion".
    :rtype: dict
    """
    query = "SELECT * FROM version"
    result_dict_list = query_dict_list(engine, query)
    return result_dict_list[0]


# TODO this should probably only return a set of basic data type, not biopython Seq.
# TODO remove duplicated function in mysqldb module.
# TODO move tests if available.
def create_seq_set(engine):
    """Create set of genome sequences currently in a MySQL database.

    :param engine: SQLAlchemy Engine object able to connect to a MySQL database.
    :type engine: Engine
    :returns: A set of unique values from phage.Sequence.
    :rtype: set
    """
    query = "SELECT Sequence FROM phage"

    # Returns a list of items, where each item is a tuple of
    # SQL data for each row in the table.
    result_list = engine.execute(query).fetchall()

    # Convert to a set of sequences.
    # Sequence data is stored as MEDIUMBLOB, so data is returned as bytes
    # "b'AATT", "b'TTCC", etc.
    result_set = set()
    for tup in result_list:
        gnm_seq = tup[0].decode("utf-8")
        gnm_seq = Seq(gnm_seq, IUPAC.ambiguous_dna).upper()
        result_set.add(gnm_seq)
    return result_set


# TODO remove duplicated function in mysqldb module.
# TODO move tests if available.
def convert_for_sql(value, check_set=set(), single=True):
    """Convert a value for inserting into MySQL.

    :param value: Value that should be checked for conversion.
    :type value: misc
    :param check_set: Set of values to check against.
    :type check_set: set
    :param single: Indicates whether single quotes should be used.
    :type single: bool
    :returns:
        Returns either "NULL" or the value encapsulated in quotes
        ("'value'" or '"value"')
    :rtype: str
    """
    if value in check_set:
        value = "NULL"
    else:
        if single == True:
            value = f"'{value}'"
        else:
            value = f'"{value}"'
    return value
