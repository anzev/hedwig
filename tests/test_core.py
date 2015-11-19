import unittest
import sys
import logging
sys.path.append('..')

from hedwig.core import Rule, ExperimentKB, load
from hedwig.stats import scorefunctions

logging.basicConfig()

class TestExperimentKB(unittest.TestCase):

    def setUp(self):
        self.data_paths = ['tests/data/n3/data.n3', 'tests/data/n3/ontology/numbers.n3']
        self.graph = load.rdf(self.data_paths)
        self.kb = ExperimentKB(self.graph, scorefunctions.lift)

    def test_examples(self):
        self.assertEqual(len(self.kb.examples), 6)

    def test_hierarchy_members(self):
        root = self.kb.get_root()
        self.assertEqual(self.kb.n_examples(), self.kb.n_members(root.label))


class TestCSVExperimentKB(TestExperimentKB):

    def setUp(self):
        self.ontology_paths = ['tests/data/csv/ontology/Hierarchy.tsv']
        self.data_path = 'tests/data/csv/Cities_clusters.csv'

        graph = load.csv(self.ontology_paths, self.data_path)
        self.kb = ExperimentKB(graph, scorefunctions.lift)

    def test_examples(self):
        self.assertEqual(len(self.kb.examples), 177)
