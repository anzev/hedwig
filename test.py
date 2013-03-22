'''
Created on Jul 20, 2012

@author: anzev
'''
from load import *
from core import *
from learner import *
import time

if __name__ == '__main__':
    start = time.time()
    f=  open('error.txt', 'w')
    print 'Loading data... ', 
    try:
        triplets = load_triplets(['../foc/eurocrisis_entities.n3', '../foc/eurocrisis_topLevel.n3', '../foc/core.n3', '../foc/ranks_weights.n3', '../foc/eurocrisis_temporal.n3'])
    except Exception, e:
        f.write(str(e))
        print 'Error loading triplet data.'
        f.close()
        exit(1)
    print 'done.'
    
    print 'Preprocessing... ',
    target_class = 'http://project-first.eu/ontology#Example'
    kb = ExperimentKB(triplets, ScoreFunctions.z_score, user_namespaces=['http://project-first.eu/ontology'])
    print 'done.'
    
    print 'Inducing... ',
    learner = Learner(kb, n=20, min_sup=30)
    #rules = learner.induce_beam()
    rules = learner.induce()
    print 'done.'
    end = time.time()
    
    f = open('rules.txt', 'w')
    for rule in rules:
        f.write('%s\n' % str(rule))
    f.close()
        
    print 'Time taken:', (end-start), 'seconds'
    
#    rule = Rule(kb, predicates=[kb.get_root()])
#    print rule
#    predicate = list(kb.predicates)[1]
#    print rule.clone_swap_with_subclass(rule.predicates[0], predicate)
#    bin_predicate = list(kb.binary_predicates)[0]
#    rule1 = rule.clone_append(bin_predicate, rule.predicates[-1], bin=True)
#    print rule1
#    predicate = list(kb.predicates)[4]
#    print rule1.clone_append(predicate, rule1.predicates[-1])
    