'''
Global settings file.
'''
import os
import logging
from rdflib import Namespace


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

# Built-in namespace
HEDWIG = Namespace('http://kt.ijs.si/hedwig#')
