'''
Significance testing methods.

@author: anze.vavpetic@ijs.si
'''
from fisher import pvalue


def is_redundant(rule, new_rule):
    '''
    Computes the redundancy coefficient of a new rule compared to its
    immediate generalization.

    Rules with a coeff > 1 are deemed non-redundant.
    '''
    return fisher(new_rule) > fisher(rule)


def fisher(rule):
    '''
    Fisher's p-value for one rule.
    '''
    N = float(len(rule.kb.examples))
    nX = float(rule.coverage)
    nY = rule.kb.distribution[rule.target]
    nXY = rule.distribution[rule.target]
    nXnotY = nX - nXY
    nnotXY = nY - nXY
    nnotXnotY = N - nXnotY - nnotXY
    return pvalue(nXY, nXnotY, nnotXY, nnotXnotY).two_tail


def apply_fisher(ruleset):
    '''
    Fisher's exact test to test rule significance.
    '''
    for rule in ruleset:
        rule.pval = fisher(rule)
