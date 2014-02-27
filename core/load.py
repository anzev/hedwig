'''
Reading input data.

@author: anze.vavpetic@ijs.si
'''
import rdflib
import json

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
                errorCount +=1
    if errorCount >0:
        raise Exception(str(errorCount) + " errors loading files:\n"+errorMsg)
    return g
