'''
Main command-line executable

@author: anze.vavpetic@ijs.si
'''
import argparse

import hedwig
from hedwig.stats import scorefunctions, adjustment
from hedwig.core.settings import VERSION, DESCRIPTION, INPUT_FORMATS


__version__ = VERSION

parser = argparse.ArgumentParser(description=DESCRIPTION)
functions = filter(lambda s: not s.startswith('_'), dir(scorefunctions))
adjustments = filter(lambda s: not s.startswith('_'), dir(adjustment))

parser.add_argument('bk_dir', metavar='BKDIR',
                    help='Background knowledge directory. The program attempts\
                          to load all RDF-type files from this directory.')

parser.add_argument('data', metavar='DATASET',
                    help='File containing the learning examples. \
                          Can be in RDF or JSON.')

parser.add_argument('-f', '--format', choices=INPUT_FORMATS,
                    help="Input file format.", default=INPUT_FORMATS[0])

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

parser.add_argument('-L', '--learner', choices=['heuristic', 'optimal'],
                    default='heuristic',
                    help='Type of learner to use.')

parser.add_argument('-O', '--optimalsubclass', action='store_true',
                    help='In each step the full hierarchy under a particular \
                          concept is searched')

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
    hedwig.run(args.__dict__, cli=True)
