'''
Module for ruleset validation.

@author: anze.vavpetic@ijs.si
'''
from adjustment import fdr
from significance import fisher


class Validate:

    def __init__(self, kb, significance_test=fisher, adjustment=fdr):
        self.kb = kb
        self.significance_test = significance_test
        self.adjustment = adjustment

    def test(self, ruleset, pval=0.05, q=0.01):
        '''
        Tests the given ruleset and returns the significant rules.
        '''
        self.significance_test(ruleset)

        if self.adjustment.__name__ == 'fdr':
            ruleset = self.adjustment(ruleset, q=q)
        else:
            ruleset = self.adjustment(ruleset)

        return filter(lambda r: r.pval <= pval, ruleset)
