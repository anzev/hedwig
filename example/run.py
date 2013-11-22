import os

os.sys.path.append(os.pardir)

from load import load_triplets
from core import ExperimentKB
from learners import Learner, ScoreFunctions


ontology_dir = './ontology/'
if __name__ == '__main__':

    data = 'data.n3'
    base_name = data.split('.')[0]

    ontology_list = []
    for root, sub_folders, files in os.walk(ontology_dir):
        ontology_list.extend(map(lambda f: os.path.join(root, f), files))
    triplets = load_triplets(ontology_list + [data])
   
    kb = ExperimentKB(triplets, ScoreFunctions.precision, 
                      user_namespaces=['http://project-first.eu/ontology'], 
                      instances_as_leaves=True)

    learner = Learner(kb, n=20, min_sup=int(0.1*kb.n_examples()), target='A', sim=0.9, depth=4)
    rules = learner.induce()
    
    for rule in rules:
        print rule
