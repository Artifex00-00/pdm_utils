.. _package_overview:


pdm\_utils package
==================

Overview
--------

The ``pdm_utils`` source code is structured within a general hierarchical strategy in mind:

    - Submodules in the 'constants' subpackage define global variables for the entire package, and they do not import any other ``pdm_utils`` or third-party modules.
    - Submodules in the 'classes' subpackage only import from the 'constants' subpackage, the 'basic' submodule in the 'functions' subpackage, or third-party modules. In general, each submodule defines one class.
    - Submodules in the 'functions' subpackage (other than the 'basic' submodule) contain functions that are either stand-alone, that rely on third-party packages, or that manipulate ``pdm_utils`` objects.
    - Submodules in the 'pipelines' subpackage contain programs that can be executed as command line tools that are meant to run from start to completion, and that can import all other submodules in the other subpackages. The most common entry point for these pipelines is the main() function. These submodules are functionalized such that custom Python tools can create alternative pipeline entry points or utilize individual functions.
    - The 'run' module' controls the command line toolkit. It is not intended to be called from other tools.



Subpackages
-----------

.. toctree::
   :maxdepth: 1

   constants <./package/subpackages/constants>
   classes <./package/subpackages/classes>
   functions <./package/subpackages/functions>
   pipelines <./package/subpackages/pipelines>

Submodules
----------

.. toctree::
   :maxdepth: 1

   run <./package/run_module>



Bio-centric object relational mapping
-------------------------------------

A subset of ``pdm_utils`` classes represents the 'back-end' bio-centric ORM that can be used to exchange data between different data sources and perform biology-related tasks with the data:

.. toctree::

  Bio-centric ORM <attribute_map>



Tutorial
--------

Refer to the brief introductory :ref:`library tutorial <library_tutorial>` to coding with the ``pdm_utils`` library.
