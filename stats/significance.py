'''
Significance testing methods.

@author: anze.vavpetic@ijs.si
'''
from fisher import pvalue


def fisher(ruleset):
    '''
    Fisher's exact test to test rule significance.
    '''
    for rule in ruleset:
        N = float(len(rule.kb.examples))
        nX = float(rule.coverage)
        nY = rule.kb.distribution[rule.target]
        nXY = rule.distribution[rule.target]
        nXnotY = nX-nXY
        nnotXY = nY-nXY
        nnotXnotY = N-nXnotY-nnotXY
        rule.pval = pvalue(nXY, nXnotY, nnotXY, nnotXnotY).two_tail
