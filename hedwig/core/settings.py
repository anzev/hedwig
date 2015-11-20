'''
Global settings file.

@author: anze.vavpetic@ijs.si
'''
import os
import logging
from rdflib import Namespace

VERSION = '0.3.0'
DESCRIPTION = '''Hedwig semantic pattern mining (anze.vavpetic@ijs.si)'''

# Logging setup
logger = logging.getLogger("Hedwig")
ch = logging.StreamHandler()
formatter = logging.Formatter("%(name)s %(levelname)s: %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# Pre-defined assets path
PAR_DIR = os.path.join(os.path.dirname(__file__), os.pardir)
ASSETS_DIR = os.path.abspath(os.path.join(PAR_DIR, 'assets'))
EXAMPLE_SCHEMA = os.path.join(ASSETS_DIR, 'builtin.n3')

# Built-in namespaces
W3C = Namespace('http://www.w3.org/')
HEDWIG = Namespace('http://kt.ijs.si/hedwig#')
DEFAULT_ANNOTATION_NAME = 'annotated_with'
GENERIC_NAMESPACE = Namespace('http://kt.ijs.si/ontology/generic#')

INPUT_FORMATS = ['n3', 'xml', 'ntriples', 'trix', 'csv']
