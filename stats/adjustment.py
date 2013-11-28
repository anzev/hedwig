'''
Multiple-testing adjustment methods.

@author: anze.vavpetic@ijs.si
'''


def holdout(ruleset):
    '''
    The holdout approach to avoid the multiple-testing problem.
    '''
    return ruleset


def fwer(ruleset):
    '''
    The Holm-Bonferroni direct adjustment method to control the FWER.
    '''
    return ruleset


def fdr(ruleset, q=0.05):
    '''
    The Benjamini-Hochberg-Yekutieli direct adjustment
    method to control the FDR.
    '''
    m = float(len(ruleset))
    max_k = 0
    sorted_rules = sorted(ruleset, key=lambda r: r.pval)
    for k, rule in enumerate(sorted_rules):
        if rule.pval > ((k+1)*q)/m:
            max_k = k
            break
    return sorted_rules[:max_k]
