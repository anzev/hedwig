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
        p = pvalue(nXY, nXnotY, nnotXY, nnotXnotY)
        rule.pval = p.two_tail
