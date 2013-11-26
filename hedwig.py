'''
Main command-line executable

@author: anze.vavpetic@ijs.si
'''
import os
import argparse
import time
import logging

from core import ExperimentKB, Rule
from learners import Learner, ScoreFunctions
from load import load_triplets
from core.settings import logger


description = '''Hedwig semantic subgroup discovery.'''

parser = argparse.ArgumentParser(description=description)
parser.add_argument('bk_dir', metavar='BKDIR',
                    help='Background knowledge directory. The program attempts\
                          to load all RDF-type files from this directory.')
parser.add_argument('data', metavar='DATASET',
                    help='File containing the learning examples. \
                          Can be in RDF or JSON.')
parser.add_argument('-o', '--output', help='Output file. If none is specified, \
                                            the results are written to stdout.')
parser.add_argument('-m', '--mode', choices=['features', 'subgroups'],
                    default='subgroups',
                    help='Running mode.')
parser.add_argument('-t', '--target', type=str,
                    help='Target class label.')
parser.add_argument('-s', '--score', choices=['precision', 'wracc', 'z_score',
                                              't_score', 'enrichment_score',
                                              'chisq'],
                    default='precision',
                    help='Score function.')
parser.add_argument('-l', '--leaves', action='store_true',
                    help='Use instance names in rule conjunctions.')
parser.add_argument('-u', '--uris', action='store_true',
                    help='Show URIs in rule conjunctions.')
parser.add_argument('-b', '--beam', default='20', type=int,
                    help='Beam size.')
parser.add_argument('-p', '--support', default='0.1', type=float,
                    help='Minimum support.')
parser.add_argument('-d', '--depth', default='4', type=int,
                    help='Maximum number of conjunctions.')
parser.add_argument("-v", "--verbose", help="Increase output verbosity.",
                    action="store_true")


if __name__ == '__main__':
    args = parser.parse_args()

    logger.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    logger.info('Starting Hedwig')
    start = time.time()

    data = args.data
    base_name = data.split('.')[0]

    # Walk the dir to find BK files
    ontology_list = []
    for root, sub_folders, files in os.walk(args.bk_dir):
        ontology_list.extend(map(lambda f: os.path.join(root, f), files))

    logger.info('Building a graph from ontologies and data')
    graph = load_triplets(ontology_list + [data])
    score_func = getattr(ScoreFunctions, args.score)

    logger.info('Building the knowledge base')
    kb = ExperimentKB(graph, score_func,
                      user_namespaces=[],
                      instances_as_leaves=args.leaves)

    logger.info('Starting learner')
    learner = Learner(kb,
                      n=args.beam,
                      min_sup=int(args.support*kb.n_examples()),
                      target=args.target,
                      depth=args.depth,
                      sim=0.9)
    rules = learner.induce()

    logger.info('Outputing results')
    rules_report = Rule.ruleset_report(rules, show_uris=args.uris)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(rules_report)
    else:
        print rules_report

    end = time.time()
    logger.info('Finished in %d seconds' % (end-start))
