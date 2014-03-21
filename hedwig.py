'''
Main command-line executable

@author: anze.vavpetic@ijs.si
'''
import os
import argparse
import time
from datetime import datetime
import logging
import json

from core import ExperimentKB, Rule
from learners import Learner
from stats import scorefunctions, adjustment, significance, Validate
from core.load import load_graph
from core.settings import logger


__version__ = '0.2.0b'

description = '''Hedwig semantic pattern mining (anze.vavpetic@ijs.si)'''
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

parser.add_argument('-c', '--covered', help='File to write IDs of covered \
                                             examples.')

parser.add_argument('-m', '--mode', choices=['features', 'subgroups'],
                    default='subgroups',
                    help='Running mode.')

parser.add_argument('-t', '--target',
                    help='Target class label. If it is not specified, rules \
                          produced for each class label.')

parser.add_argument('-s', '--score', choices=functions, default='lift',
                    help='Score function.')

parser.add_argument('-n', '--negations', action='store_true',
                    help='Use negations.')

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


def _parameters_report(args, start, time_taken):
    sep = '-'*40 + '\n'
    rep = description + '\n' +\
        'Version: %s' % __version__ + '\n' +\
        'Start: %s' % start + '\n' +\
        'Time taken: %.2f seconds' % time_taken + '\n' +\
        'Parameters:' + '\n'

    for arg, val in args.items():
        rep += '\t%s=%s\n' % (arg, str(val))
    rep = sep + rep + sep

    return rep


def generate_rules_report(kwargs, rules_per_target,
                          human=lambda label, rule: label):
    rules_report = ''
    for _, rules in rules_per_target:
        if rules:
            rules_report += Rule.ruleset_report(rules, show_uris=kwargs['uris'],
                                                human=human)
            rules_report += '\n'
    if not rules_report:
        rules_report = 'No significant rules found'
    return rules_report


def run(kwargs, cli=False):

    if cli:
        logger.setLevel(logging.DEBUG if kwargs['verbose'] else logging.INFO)
    else:
        logger.setLevel(logging.NOTSET)

    logger.info('Starting Hedwig')
    start = time.time()
    start_date = datetime.now().isoformat()

    graph = build_graph(kwargs)

    logger.info('Building the knowledge base')
    score_func = getattr(scorefunctions, kwargs['score'])
    kb = ExperimentKB(graph, score_func, instances_as_leaves=kwargs['leaves'])

    validator = Validate(kb, significance_test=significance.apply_fisher,
                         adjustment=getattr(adjustment, kwargs['adjust']))

    rules_per_target = run_learner(kwargs, kb, validator)
    rules_report = generate_rules_report(kwargs, rules_per_target)
    

    end = time.time()
    time_taken = end-start
    logger.info('Finished in %d seconds' % time_taken)

    logger.info('Outputing results')

    if kwargs['covered']:
        with open(kwargs['covered'], 'w') as f:
            examples = Rule.ruleset_examples_json(rules_per_target)
            f.write(json.dumps(examples, indent=2))

    parameters_report = _parameters_report(kwargs, start_date, time_taken)
    if kwargs['output']:
        with open(kwargs['output'], 'w') as f:
            f.write(parameters_report)
            f.write(rules_report)
    elif cli:
        print parameters_report
        print rules_report

    return rules_per_target


def build_graph(kwargs):
    data = kwargs['data']
    base_name = data.split('.')[0]

    # Walk the dir to find BK files
    ontology_list = []
    for root, sub_folders, files in os.walk(kwargs['bk_dir']):
        ontology_list.extend(map(lambda f: os.path.join(root, f), files))

    try:
        graph = load_graph(ontology_list + [data])
    except Exception, e:
        print e
        exit(1)
    return graph


def run_learner(kwargs, kb, validator):

    if kb.is_discrete_target():
        targets = kb.class_values if not kwargs['target'] else [kwargs['target']]
    else:
        targets = [None]

    rules_report = ''
    rules_per_target = []

    for target in targets:
        if target:
            logger.info('Starting learner for target \'%s\'' % target)
        else:
            logger.info('Ranks detected - starting learner.')
        learner = Learner(kb,
                          n=kwargs['beam'],
                          min_sup=int(kwargs['support']*kb.n_examples()),
                          target=target,
                          depth=kwargs['depth'],
                          sim=0.9,
                          use_negations=kwargs['negations'])
        rules = learner.induce()

        if kb.is_discrete_target():
            if kwargs['adjust'] == 'fdr':
                logger.info('Validating rules, FDR = %.3f' % kwargs['FDR'])
            else:
                logger.info('Validating rules, alpha = %.3f' % kwargs['alpha'])
            rules = validator.test(rules, alpha=kwargs['alpha'], q=kwargs['FDR'])

        rules_per_target.append((target, rules))

    return rules_per_target


if __name__ == '__main__':
    args = parser.parse_args()
    run(args.__dict__, cli=True)
