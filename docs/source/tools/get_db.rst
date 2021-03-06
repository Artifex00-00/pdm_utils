.. _getdb:

get_db: download and install a database
=======================================


The Hatfull lab server hosts the primary actinobacteriophage database instance, Actinobacteriophage, which is routinely updated with new genomics data, as well as databases that have been frozen for publication. These databases can be downloaded and installed using the ``pdm_utils get_db`` tool.

To view and interactively select the list of available databases on the Hatfull lab server::

    > python3 -m pdm_utils get_db server

To download and install the current version of the Actinobacteriophage database::

    > python3 -m pdm_utils get_db server -db Actinobacteriophage

The -db argument 'Actinobacteriophage' indicates the name of the database to download from the server, and it will install it under the same name in your local MySQL. The database will be downloaded, installed, and then the file will be removed.

.. note::
    This will overwrite an existing Actinobacteriophage database, if it exists.


To download and install a database from a non-standard server, specify the URL::

    > python3 -m pdm_utils get_db server -db PhageDatabaseName -u http://custom/server/website 



Databases can be downloaded and installed in two steps, which can be used to install a database under a new name:

    1. First download the database sql and version files from the Hatfull server using the '-d' and '-v' flags. This will save the database to your local computer as a SQL file (e.g. Actinobacteriophage.sql) without installing it in MySQL. Also specify where the file should be downloaded using the '-o' flag (if omitted, the default is the /tmp/ directory)::

        > python3 -m pdm_utils get_db server -db Actinobacteriophage -o ./ -d -v


    2. Next, indicate the new name of the database to be created (e.g. NewDB), indicate that a local file will be used with 'file' , and indicate the path to the downloaded SQL file::

        > python3 -m pdm_utils get_db NewDB file ./downloaded_db/Actinobacteriophage.sql


Use of a :ref:`config_file` can automate the pipeline so that user input such as MySQL credentials or server URL is not needed::

    > python3 -m pdm_utils get_db server -db Actinobacteriophage -o ./ -d -v -c config_file.txt
