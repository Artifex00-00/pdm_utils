"""Integration unittests for the filter module"""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from networkx import Graph
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql.elements import BinaryExpression
from sqlalchemy.sql.elements import BooleanClauseList

from pdm_utils.classes.alchemyhandler import AlchemyHandler
from pdm_utils.classes.filter import Filter
from pdm_utils.functions import cartography
from pdm_utils.functions import querying

# Import helper functions to build mock database
unittest_file = Path(__file__)
test_dir = unittest_file.parent.parent
if str(test_dir) not in set(sys.path):
    sys.path.append(str(test_dir))
import test_db_utils

# pdm_anon, pdm_anon, and pdm_test_db
user = test_db_utils.USER
pwd = test_db_utils.PWD
db = test_db_utils.DB

class TestFilter(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        test_db_utils.create_filled_test_db()

    @classmethod
    def tearDownClass(self):
        test_db_utils.remove_db()

    def setUp(self):
        alchemist = AlchemyHandler()
        alchemist.username=user
        alchemist.password=pwd
        alchemist.database=db
        alchemist.connect()
        self.alchemist = alchemist

        self.db_filter = Filter(alchemist=self.alchemist)

        self.phage = self.alchemist.metadata.tables["phage"]
        self.gene = self.alchemist.metadata.tables["gene"]
        self.trna = self.alchemist.metadata.tables["trna"]

        self.PhageID = self.phage.c.PhageID
        self.Cluster = self.phage.c.Cluster
        self.Subcluster = self.phage.c.Subcluster
        
        self.Notes = self.gene.c.Notes

    def tearDown(self):
        self.alchemist.clear()

    def test_and__1(self):
        """Verify that and_() creates a dictionary key as expected.
        """
        self.db_filter.and_("phage.PhageID=Myrna")

        or_block = self.db_filter.filters[0]
        self.assertTrue("phage.PhageID=Myrna" in or_block.keys())

    def test_and__2(self):
        """Verify that and_() stores BinaryExpression data as expected.
        """

        self.db_filter.and_("phage.PhageID=Myrna")

        or_block = self.db_filter.filters[0]
        self.assertTrue(isinstance(or_block, dict))

        where_clauses = or_block["phage.PhageID=Myrna"]
        self.assertTrue(isinstance(where_clauses, BinaryExpression))

    def test_and_3(self):
        """Verify that and_() recognizes previous and_() data.
        """
        self.db_filter.and_("phage.PhageID =  Myrna")
        self.db_filter.and_("phage.PhageID=Myrna")
        self.db_filter.and_("phage.PhageID=D29")

        or_block = self.db_filter.filters[0]
        self.assertEqual(len(or_block), 2)

    def test_and_4(self):
        """Verify that and_() recognizes and stores IN-type clauses.
        """
        self.db_filter.and_("phage.PhageID IN (D29, Trixie, Myrna)")

        or_block = self.db_filter.filters[0]
        self.assertTrue("phage.PhageIDIN(D29,Trixie,Myrna)")

    def test_remove_1(self):
        """Verify that remove() removes dictionary entry after depleted.
        """
        self.db_filter.and_("phage.PhageID=Myrna")
        self.db_filter.remove("phage.PhageID=Myrna")
        self.assertEqual(self.db_filter.filters, [{}])

    def test_remove_2(self):
        """Verify that remove() conserves dictionary entry if not depleted.
        """
        self.db_filter.and_("phage.PhageID=Myrna")
        self.db_filter.and_("phage.PhageID=D29")

        self.db_filter.remove("phage.PhageID=Myrna")

        or_block = self.db_filter.filters[0]
        where_clauses = or_block["phage.PhageID=D29"]

        self.assertEqual(where_clauses.right.value, "D29")

    def test_add_1(self):
        """Verify that add() creates a dictionary key as expected.
        """
        self.db_filter.add("phage.PhageID=Myrna")

        or_block = self.db_filter.filters[0]
        self.assertTrue("phage.PhageID=Myrna" in or_block.keys())

    def test_add_2(self):
        """Verify that add() creates multiple keys as expected.
        """
        self.db_filter.add("phage.PhageID=Myrna AND phage.PhageID = Trixie")

        or_block = self.db_filter.filters[0]

        self.assertTrue(len(or_block) == 2)

        self.assertTrue("phage.PhageID=Myrna" in or_block.keys())
        self.assertTrue("phage.PhageID=Trixie" in or_block.keys())

    def test_add_3(self):
        """Verify that add() creates multiple or blocks as expected.
        """
        self.db_filter.add("phage.PhageID=Myrna OR phage.PhageID = Trixie")

        self.assertTrue(len(self.db_filter.filters) == 2)

        first_or_block = self.db_filter.filters[0]
        second_or_block = self.db_filter.filters[1]

        self.assertTrue("phage.PhageID=Myrna" in first_or_block.keys())
        self.assertFalse("phage.PhageID=Trixie" in first_or_block.keys())

        self.assertFalse("phage.PhageID=Myrna" in second_or_block.keys())
        self.assertTrue("phage.PhageID=Trixie" in second_or_block.keys())

    def test_parenthesize_1(self):
        """Verify that parenthesize() condenses multiple or blocks.
        """
        self.db_filter.add("phage.PhageID = Myrna OR phage.PhageID = Trixie")
        self.db_filter.parenthesize()

        self.assertTrue(len(self.db_filter.filters) == 1)

        or_block = self.db_filter.filters[0]

        self.assertTrue("parenthetical" in or_block.keys())

    def test_parenthesize_2(self):
        """Verify that parenthesize() filters produce the expected conditionals.
        """
        self.db_filter.add("phage.PhageID = Myrna OR phage.PhageID = Trixie")
        self.db_filter.parenthesize()

        self.db_filter.key = "phage.PhageID"
        self.db_filter.update()

        self.assertTrue("Trixie" in self.db_filter.values)
        self.assertTrue("Myrna" in self.db_filter.values)
        self.assertTrue(len(self.db_filter.values) == 2)
    
    def test_parenthesize_3(self):
        """Verify that parenthesize() allows for additional filter stacking.
        """
        self.db_filter.add("phage.PhageID = 'D29' OR phage.PhageID = 'Trixie'")
        self.db_filter.parenthesize()
        self.db_filter.add("phage.Cluster = 'A'")

        self.db_filter.key = "phage.PhageID"
        self.db_filter.update()

        self.assertTrue("Trixie" in self.db_filter.values)
        self.assertTrue("D29" in self.db_filter.values)
        self.assertTrue(len(self.db_filter.values) == 2)

    def test_parenthesize_4(self):
        """Verify that parenthesize() prioritizes over OR conditionals.
        """
        self.db_filter.add("phage.PhageID = Myrna OR phage.PhageID = Trixie")
        self.db_filter.parenthesize()
        self.db_filter.add("phage.Cluster = 'A'")

        self.db_filter.key = "phage.PhageID"
        self.db_filter.update()

        self.assertTrue("Trixie" in self.db_filter.values)
        self.assertFalse("Myrna" in self.db_filter.values)
        self.assertTrue(len(self.db_filter.values) == 1)

    def test_get_column_1(self):
        """Verify that get_column() converts string column input.
        """
        self.db_filter.key = self.Cluster

        column = self.db_filter.get_column("phage.PhageID")

        self.assertEqual(column, self.PhageID)

    def test_get_column_2(self):
        """Verify that get_column() conserves Column input.
        """
        self.db_filter.key = self.Cluster

        column = self.db_filter.get_column(self.PhageID)

        self.assertEqual(column, self.PhageID)

    def test_get_column_3(self):
        """Verify that get_column() raises TypeError.
        get_column() should raise TypeError when column input is
        neither a string or a Column.
        """
        self.db_filter.key = self.Cluster

        with self.assertRaises(TypeError):
            self.db_filter.get_column(None)

    def test_build_where_clauses_1(self):
        """Verify that build_where_clauses() forms list of expected length.
        """
        self.db_filter.and_("phage.PhageID=Myrna")
        self.db_filter.and_("phage.PhageID=D29")

        queries = self.db_filter.build_where_clauses()

        self.assertEqual(len(queries[0]), 2)

    def test_build_where_clauses_2(self):
        """Verify that build_where_clauses() forms list of BinaryExpressions.
        """
        self.db_filter.and_("phage.PhageID=Myrna")
        self.db_filter.and_("phage.PhageID=D29")

        queries = self.db_filter.build_where_clauses()

        for query in queries:
            self.assertTrue(isinstance(query, BooleanClauseList))

    def test_build_values_1(self):
        """Verify that build_values() does not exclude values as expected.
        """
        self.db_filter.key = self.PhageID

        values = self.db_filter.build_values()

        self.assertTrue("Myrna" in values)
        self.assertTrue("D29" in values)
        self.assertTrue("Alice" in values)
        self.assertTrue("Trixie" in values)

    def test_build_values_2(self):
        """Verify that build_values() utilizes WHERE clauses as expected.
        """
        self.db_filter.key = self.PhageID

        where_clause = (self.Cluster == "A")
        values = self.db_filter.build_values(where=where_clause)

        self.assertTrue("D29" in values)
        self.assertTrue("Trixie" in values)
        self.assertFalse("Myrna" in values)
        self.assertFalse("Alice" in values)

    def test_build_values_3(self):
        """Verify that build_values() creates DISTINCT values as expected.
        """
        self.db_filter.key = self.Cluster

        where_clause = (self.Subcluster == "A2")
        values = self.db_filter.build_values(where=where_clause)

        self.assertEqual(len(values), 1)
        self.assertEqual(values, ["A"])

    def test_build_values_4(self):
        """Verify that build_values() recognizes bytes-type column data.
        """
        self.db_filter.key = self.Notes

        values = self.db_filter.build_values()

        self.assertTrue(isinstance(values[0], str))

    def test_query_1(self):
        """Verify that query() creates instances as expected.
        """
        self.db_filter.key = "phage.PhageID"
        self.db_filter.values = ["Trixie", "D29"]
        self.db_filter.refresh()

        instances = self.db_filter.query("phage")

        instance_ids = []
        for instance in instances:
            instance_ids.append(instance.PhageID)

        self.assertTrue("Trixie" in instance_ids)
        self.assertTrue("D29" in instance_ids)
        self.assertFalse("Myrna" in instance_ids)

    def test_query_2(self):
        """Verify that query() creates instances as expected.
        """
        self.db_filter.key = "phage.PhageID"
        self.db_filter.values = ["Trixie", "D29"]
        self.db_filter.refresh()

        instances = self.db_filter.query("gene")

        instance_ids = set()

        for instance in instances:
            instance_ids.add(instance.phage.PhageID)

        instance_ids = list(instance_ids)

        self.assertTrue("Trixie" in instance_ids)
        self.assertTrue("D29" in instance_ids)
        self.assertFalse("Myrna" in instance_ids)

    def test_transpose_1(self):
        """Verify that transpose() utilizes Filter values as expected.
        """
        self.db_filter.values = ["Myrna"]
        self.db_filter.key = self.PhageID

        self.db_filter.refresh()

        clusters = self.db_filter.transpose("phage.Cluster")

        self.assertEqual(clusters, ["C"])

    def test_transpose_2(self):
        """Verify that transpose() can optionally create dict return value.
        """
        self.db_filter.values = ["Myrna"]
        self.db_filter.key = self.PhageID

        self.db_filter.refresh()

        clusters_dict = self.db_filter.transpose(self.Cluster, return_dict=True)

        self.assertEqual(clusters_dict["Cluster"], ["C"])

    def test_transpose_3(self):
        """Verify that transpose() can alter Filter properties as expected.
        """
        self.db_filter.values = ["Myrna"]
        self.db_filter.key = self.PhageID

        self.db_filter.refresh()

        self.db_filter.transpose("phage.Cluster", set_values=True)

        self.assertEqual(self.db_filter.key, self.Cluster)
        self.assertEqual(self.db_filter.values, ["C"])

    def test_transpose_4(self):
        """Verify that transpose() filter parameter functions as expected.
        """
        self.db_filter.values = ["Myrna", "D29"]
        self.db_filter.key = self.PhageID

        self.db_filter.add("gene.GeneID = Myrna_CDS_28")
        values = self.db_filter.transpose("gene.GeneID", filter=True)

        self.assertEqual(len(values), 1)
        self.assertEqual(values[0], "Myrna_CDS_28")

    def test_mass_transpose_1(self):
        """Verify that mass_tranpose() returns DISTINCT values as expected.
        """
        self.db_filter.values = ["Myrna"]
        self.db_filter.key = self.PhageID

        self.db_filter.refresh()

        myrna_data = self.db_filter.mass_transpose(["phage.HostGenus",
                                              "phage.Cluster",
                                              "gene.Notes"])

        self.assertTrue(len(myrna_data) == 3 )
        self.assertTrue(isinstance(myrna_data, dict))

        self.assertEqual(myrna_data["HostGenus"], ["Mycobacterium"])
        self.assertEqual(myrna_data["Cluster"], ["C"])

    def test_mass_transpose_2(self):
        """Verify that mass_tranpose() utilizes all values as expected.
        """
        self.db_filter.values = ["Myrna", "Trixie"]
        self.db_filter.key = self.PhageID

        self.db_filter.refresh()

        data = self.db_filter.mass_transpose(["phage.HostGenus",
                                        "phage.Cluster",
                                        "gene.Notes"])

        self.assertTrue(len(data) == 3)
        self.assertTrue(isinstance(data, dict))

        self.assertEqual(data["HostGenus"], ["Mycobacterium"])
        self.assertEqual(data["Cluster"], ["C", "A"])

    def test_retrieve_1(self):
        """Verify that retrieve() separates data as expected.
        """
        self.db_filter.values = ["Myrna", "Trixie"]
        self.db_filter.key = self.PhageID

        self.db_filter.refresh()

        data = self.db_filter.retrieve(["phage.HostGenus",
                                        "phage.Cluster"])

        myrna_data = data["Myrna"]
        self.assertEqual(myrna_data["HostGenus"], ["Mycobacterium"])
        self.assertEqual(myrna_data["Cluster"], ["C"])

        trixie_data = data["Trixie"]
        self.assertEqual(trixie_data["HostGenus"], ["Mycobacterium"])
        self.assertEqual(trixie_data["Cluster"], ["A"])

    def test_retrieve_2(self):
        """Verify that retrieve() separates data as expected.
        """
        self.db_filter.values = ["A", "C"]
        self.db_filter.key = self.Cluster

        self.db_filter.refresh()

        data = self.db_filter.retrieve(["phage.Cluster", "phage.PhageID"])

        a_data = data["A"]
        self.assertEqual(a_data["Cluster"], ["A"])
        self.assertTrue("Trixie" in a_data["PhageID"])
        self.assertFalse("Myrna" in a_data["PhageID"])

        c_data = data["C"]
        self.assertEqual(c_data["Cluster"], ["C"])
        self.assertFalse("Trixie" in c_data["PhageID"])
        self.assertTrue("Myrna" in c_data["PhageID"])

    def test_retrieve_3(self):
        """Verify that test_retrieve() can retrieve by byte-type columns.
        """
        self.db_filter.key = "gene.Notes"
        self.db_filter.values = ["helix-turn-helix DNA binding protein", 
                                 "RNA binding protein"]

        retrieve_results = self.db_filter.retrieve("gene.PhamID")
        self.assertTrue("helix-turn-helix DNA binding protein" \
                                 in retrieve_results.keys())
        self.assertTrue("RNA binding protein" in retrieve_results.keys())
        

    def test_refresh_1(self):
        """Verify that refresh() eliminates invalid data.
        """
        self.db_filter.key = self.PhageID
        self.db_filter.values = ["Myrna", "D29", "Sheetz"]
        self.db_filter.refresh()

        self.assertTrue("Myrna" in self.db_filter.values)
        self.assertTrue("D29" in self.db_filter.values)
        self.assertFalse("Sheetz" in self.db_filter.values)
 
    def test_update_1(self):
        """Verify that update() filters out values.
        """
        self.db_filter.key = self.PhageID
        self.db_filter.values = ["Myrna", "D29"]
        self.db_filter.and_("phage.PhageID=Myrna")
        self.db_filter.update()

        self.assertTrue("Myrna" in self.db_filter.values)
        self.assertFalse("D29" in self.db_filter.values)

    def test_sort_1(self):
        """Verify that sort() orders values as expected.
        """
        self.db_filter.key = self.PhageID
        self.db_filter.values = ["Myrna", "D29"]
        self.db_filter.sort(self.PhageID)

        self.assertTrue("Myrna" in self.db_filter.values)
        self.assertTrue("D29" in self.db_filter.values)
        self.assertEqual(self.db_filter.values[0], "D29")

    def test_sort_2(self):
        """Verify that sort() orders values with multiple sort columns.
        """
        self.db_filter.key = self.PhageID
        self.db_filter.values = ["Myrna", "D29", "Alice"]
        self.db_filter.sort([self.Cluster, self.PhageID])

        self.assertTrue("Myrna" in self.db_filter.values)
        self.assertTrue("D29" in self.db_filter.values)
        self.assertTrue("Alice" in self.db_filter.values)
        
        self.assertEqual(self.db_filter.values[0], "D29")
        self.assertEqual(self.db_filter.values[1], "Alice")

    def test_group_1(self):
        """Verify that group() creates separate groups as expected.
        """
        self.db_filter.key = self.PhageID
        self.db_filter.values = ["Myrna", "D29"]
        group_results = self.db_filter.group(self.PhageID)

        self.assertTrue("Myrna" in group_results.keys())
        self.assertTrue("Myrna" in group_results["Myrna"])

        self.assertTrue("D29" in group_results.keys())
        self.assertTrue("D29" in group_results["D29"])

    def test_group_2(self):
        """Verify that group() recognizes similarities in values as expected.
        """
        self.db_filter.key = self.PhageID
        self.db_filter.values = ["Myrna", "D29"]
        group_results = self.db_filter.group("phage.HostGenus")

        self.assertTrue("Mycobacterium" in group_results.keys())

        self.assertTrue("Myrna" in group_results["Mycobacterium"])
        self.assertTrue("D29" in group_results["Mycobacterium"])

    def test_group_3(self):
        """Verify that group() recognizes differences in values as expected.
        """
        self.db_filter.key = self.PhageID
        self.db_filter.values = ["Myrna", "D29", "Trixie"]
        group_results = self.db_filter.group("phage.Cluster")

        self.assertTrue("A" in group_results.keys())
        self.assertTrue("C" in group_results.keys())

        self.assertTrue("Myrna" in group_results["C"])
        self.assertTrue("D29" in group_results["A"])
        self.assertTrue("Trixie" in group_results["A"])

    def test_group_4(self):
        """Verify that group() can group by byte-type columns.
        """
        self.db_filter.key = "gene.GeneID"
        self.db_filter.values = ["Myrna_CDS_1", "D29_CDS_1", "Trixie_CDS_3"]
        group_results = self.db_filter.group("gene.Notes")

if __name__ == "__main__":
    unittest.main()
