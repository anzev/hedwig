'''
Main command-line executable

@author: anze.vavpetic@ijs.si
'''
import os
import argparse
import time
import logging

from core import ExperimentKB, Rule
from learners import Learner
from stats import scorefunctions, adjustment, significance, Validate
from core.load import rdf
from core.settings import logger


description = '''Hedwig semantic subgroup discovery.'''
parser = argparse.ArgumentParser(description=description)
functions = filter(lambda s: not s.startswith('_'), dir(scorefunctions))
adjustments = filter(lambda s: not s.startswith('_'), dir(adjustment))

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

parser.add_argument('-t', '--target',
                    help='Target class label. If it is not specified, rules \
                          produced for each class label.')

parser.add_argument('-s', '--score', choices=functions, default='lift',
                    help='Score function.')

parser.add_argument('-A', '--alpha', default='0.05', type=float,
                    help='P-value threshold; applies if "--adjust fwer" \
                          is used.')

parser.add_argument('-a', '--adjust', default='fwer', choices=adjustments,
                    help='Adjustment method for the multiple-testing problem.')

parser.add_argument('-q', '--FDR', default='0.05', type=float,
                    help='Max false discovery rate; applies only if \
                          "--adjust fdr" is used.')

parser.add_argument('-l', '--leaves', action='store_true',
                    help='Use instance names in rule conjunctions.')

parser.add_argument('-u', '--uris', action='store_true',
                    help='Show URIs in rule conjunctions.')

parser.add_argument('-b', '--beam', default='20', type=int,
                    help='Beam size.')

parser.add_argument('-S', '--support', default='0.1', type=float,
                    help='Minimum support.')

parser.add_argument('-d', '--depth', default='5', type=int,
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
    graph = rdf(ontology_list + [data])
    score_func = getattr(scorefunctions, args.score)

    logger.info('Building the knowledge base')
    kb = ExperimentKB(graph, score_func, instances_as_leaves=args.leaves)

    validator = Validate(kb, significance_test=significance.apply_fisher,
                         adjustment=getattr(adjustment, args.adjust))

    rules_report = ''
    targets = kb.class_values if not args.target else [args.target]
    for target in targets:
        logger.info('Starting learner for target \'%s\'' % target)
        learner = Learner(kb,
                          n=args.beam,
                          min_sup=int(args.support*kb.n_examples()),
                          target=target,
                          depth=args.depth,
                          sim=0.9)
        rules = learner.induce()

        if args.adjust == 'fdr':
            logger.info('Validating rules, FDR = %.3f' % args.FDR)
        else:
            logger.info('Validating rules, alpha = %.3f' % args.alpha)
        rules = validator.test(rules, alpha=args.alpha, q=args.FDR)

        if rules:
            rules_report += Rule.ruleset_report(rules, show_uris=args.uris)
            rules_report += '\n'

    if not rules_report:
        rules_report = 'No significant rules found'

    logger.info('Outputing results')
    if args.output:
        with open(args.output, 'w') as f:
            f.write(rules_report)
    else:
        print rules_report

    end = time.time()
    logger.info('Finished in %d seconds' % (end-start))
