'''
Reading input data.

@author: anze.vavpetic@ijs.si
'''
import rdflib
import json
import hashlib
import os
import cPickle

from core.settings import logger
from example import Example


def json_examples(path):
    '''
    Loads from a json file of examples.
    '''
    input = json.loads(open(path).read())
    examples = []
    for ex in input:
        id, label, rank, annotations = ex['id'], ex['label'], ex['rank'], ex['annotations']
        examples.append(Example(id, label, rank, annotations))
    return examples


def rdf(paths, def_format='n3'):
    '''
    Loads the ontology into an rdf graph.
    '''
    g = rdflib.graph.Graph()
    errorMsg = ''
    errorCount = 0
    for path in paths:
        if path.endswith(def_format):
            try:
                g.parse(path, format=def_format)
            except Exception, e:
                errorMsg = errorMsg + 'Error parsing file: ' + path +'.\n' + str(e) + '\n\n'
                errorCount += 1
    if errorCount > 0:
        raise Exception(str(errorCount) + " errors loading files:\n" + errorMsg)
    return g


def load_graph(paths, def_format='n3'):
    logger.info('Calculating data checksum')
    md5 = _md5_checksum(filter(lambda path: path.endswith(def_format), paths))

    cached_fn = '.%s' % md5
    if os.path.exists(cached_fn):
        logger.info('Loading cached graph structure')
        g = _load_cached_graph(cached_fn)
    else:
        logger.info('Building graph structure')
        g = rdf(paths, def_format=def_format)
        _save_graph_to_cache(g, cached_fn)
    return g


def _md5_checksum(paths):
    md5 = hashlib.md5()
    for path in paths:
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(2**20), b''):
                    md5.update(chunk)
    return md5.hexdigest()


def _load_cached_graph(fn):
    g = cPickle.load(open(fn))
    return g


def _save_graph_to_cache(g, fn):
    with open(fn, 'w') as f:
        cPickle.dump(g, f)
