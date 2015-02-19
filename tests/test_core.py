import unittest
import sys
sys.path.append('..')

from core import Rule, ExperimentKB, load
from stats import scorefunctions


class TestExperimentKB(unittest.TestCase):

    def setUp(self):
        self.data_paths = ['tests/data/data.n3', 'tests/data/ontology/numbers.n3']
        self.graph = load.rdf(self.data_paths)
        self.kb = ExperimentKB(self.graph, scorefunctions.lift)

    def test_examples(self):
        self.assertEqual(len(self.kb.examples), 6)

    def test_hierarchy_members(self):
        root = self.kb.get_root()
        self.assertEqual(self.kb.n_examples()), self.kb.n_members(root.label)))
