'''
Reading input data.

@author: anzev
'''
import rdflib
import core
import json

def load_json_examples(path):
    '''
    Loads from a json file of examples.
    '''
    input = json.loads(open(path).read())
    examples = []
    for ex in input:
        id, label, rank, annotations = ex['id'], ex['label'], ex['rank'], ex['annotations']
        examples.append(core.Example(id, label, rank, annotations))
    return examples

def load_triplets(paths, def_format='n3'):
    '''
    Loads the ontology into an rdf graph.
    '''
    g = rdflib.graph.Graph()
    for path in paths:
        g.parse(path, format=def_format)
    return g
