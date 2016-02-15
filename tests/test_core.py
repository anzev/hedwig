import unittest
import sys
import logging
import urllib2
import json
from subprocess import call
from jsonschema import validate
sys.path.append('..')

from hedwig.core import Rule, ExperimentKB, load, save
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


class TestSaving(unittest.TestCase):

    def setUp(self):
        self.data_paths = ['tests/data/n3/data.n3', 'tests/data/n3/ontology/']
        self.graph = load.rdf(self.data_paths)
        self.kb = ExperimentKB(self.graph, scorefunctions.lift)
        self.schema = json.load(urllib2.urlopen('http://source.ijs.si/hbp/modelformatschema/raw/master/model_schema.json'))

    def test_save_json(self):
        call([
            'python', '-m', 'hedwig',
            self.data_paths[1],
            self.data_paths[0],
            '-l',
            '-o', 'out.json',
            '-a', 'none',
            '--nocache'
        ])
        try:
            with open('out.json') as f:
                validate(json.load(f), self.schema)
        except Exception as e:
            print str(e)
            self.assertTrue(False)
        self.assertTrue(True)
