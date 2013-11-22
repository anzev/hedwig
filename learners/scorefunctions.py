'''
Score function definitions.

@author: anze.vavpetic@ijs.si
'''
from math import sqrt


class ScoreFunctions:
    '''
    A collection of score functions.
    '''
    @staticmethod
    def z_score(rule):
        return sqrt(rule.coverage) * (rule.mean - rule.kb.mean) / rule.kb.sd

    @staticmethod
    def t_score(rule):
        return sqrt(rule.coverage) * (rule.mean - rule.kb.mean) / rule.sd

    @staticmethod
    def enrichment_score(rule):
        # The enrichment score of a rule covering all examples is 1
        if rule.coverage == rule.kb.n_examples():
            return 1.0
        if rule.coverage == 0:
            return - 1 / float(rule.kb.n_examples())
        increment = {}
        incr1 = 1 / float(rule.coverage)
        incr2 = 1 / float(rule.kb.n_examples() - rule.coverage)
        max_diff = 0
        # All examples
        for ex in rule.kb.examples:
            increment[ex] = -incr2
        for ex in rule.examples():
            increment[ex] = incr1
        partial = 0
        for ex in rule.kb.examples:
            partial += increment[ex]
            if partial > max_diff:
                max_diff = partial
        return max_diff

    @staticmethod
    def wracc(rule):
        nX = rule.coverage
        N = len(rule.kb.examples)
        nXY = rule.distribution[rule.target]
        nY = rule.kb.distribution[rule.target]
        if nX:
            return nX / float(N) * (nXY/float(nX) - nY/float(N))
        else:
            return 0

    @staticmethod
    def precision(rule):
        nX = rule.coverage
        nXY = rule.distribution[rule.target]
        if nX:
            return nXY/float(nX)
        else:
            return 0

    @staticmethod
    def chisq(rule):
        N = len(rule.kb.examples)
        z = rule.distribution[rule.target]/float(N)
        x = rule.coverage/float(N)
        y = rule.kb.distribution[rule.target]/float(N)
        if x not in [0, 1] and y not in [0, 1]:
            return N*(z - x*y)**2 / float(x*y*(1 - x)*(1 - y))
        else:
            return 0
