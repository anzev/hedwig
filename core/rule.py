'''
The rule class.

@author: anze.vavpetic@ijs.si
'''
from collections import defaultdict

from predicate import UnaryPredicate, BinaryPredicate
from example import Example
from helpers import avg, std


class Rule:
    '''
    Represents a rule, along with its description, examples and statistics.
    '''
    def __init__(self, kb, predicates=[], target=None):
        self.predicates = predicates
        self.kb = kb
        self.covered_examples = kb.get_full_domain()
        self.target_type = kb.target_type
        self.target = target

        # Allow only unary predicates
        for pred in predicates:
            if isinstance(pred, UnaryPredicate):
                self.covered_examples &= pred.domain[pred.input_var]

        self.head_var = None
        if self.predicates:
            self.head_var = self.predicates[0].input_var

        # Dictionary of predicates that share a certain variable
        self.shared_var = {self.head_var: self.predicates}

        # Predicates that currently can be specialized
        self.latest_var = self.head_var

        # Statistics
        self.score = -1
        self.coverage = -1
        self.mean = -1
        self.sd = -1
        self.distribution = {}
        self.__refresh_coverage()
        self.__refresh_statistics()

        # Validation
        self.pval = -1

    def clone(self):
        '''
        Returns a clone of this rule. The predicates themselves are NOT cloned.
        '''
        new_rule = Rule(self.kb, target=self.target)
        new_rule.predicates = self.predicates[:]
        new_rule.covered_examples = self.covered_examples
        new_rule.latest_var = self.latest_var
        new_rule.head_var = self.head_var
        new_rule.shared_var = {}
        for var in self.shared_var:
            new_rule.shared_var[var] = self.shared_var[var][:]
        return new_rule

    def clone_negate(self, target_pred):
        '''
        Returns a copy of this rule where 'taget_pred' is negated.
        '''
        new_rule = self.clone()

        # Create the instance of the child pred
        producer_pred = target_pred.producer_predicate
        var_name = target_pred.input_var
        members = target_pred.domain[target_pred.input_var].copy()
        members.invert()
        neg_pred = UnaryPredicate(target_pred.label,
                                  members,
                                  self.kb,
                                  producer_pred=producer_pred,
                                  custom_var_name=var_name,
                                  negated=True)

        new_rule._replace_predicate(target_pred, neg_pred)
        return new_rule

    def clone_swap_with_subclass(self, target_pred, child_pred_label):
        '''
        Returns a copy of this rule where
        'target_pred' is swapped for 'child_pred_label'.
        '''
        new_rule = self.clone()

        # Create the instance of the child pred
        producer_pred = target_pred.producer_predicate
        var_name = target_pred.input_var
        child_pred = UnaryPredicate(child_pred_label,
                                    self.kb.get_members(child_pred_label),
                                    self.kb,
                                    producer_pred=producer_pred,
                                    custom_var_name=var_name)

        new_rule._replace_predicate(target_pred, child_pred)
        return new_rule

    def clone_append(self, predicate_label, producer_pred, bin=False):
        '''
        Returns a copy of this rule where 'predicate_label'
        is appended to the rule.
        '''
        if not bin:
            new_rule = self.clone()
            predicate = UnaryPredicate(predicate_label,
                                       self.kb.get_members(predicate_label),
                                       self.kb,
                                       producer_pred=producer_pred)
            new_rule.predicates.append(predicate)
            new_rule.shared_var[producer_pred.output_var].append(predicate)
        else:
            new_rule = self.clone()
            predicate = BinaryPredicate(predicate_label,
                                        self.kb.get_members(predicate_label),
                                        self.kb,
                                        producer_pred=producer_pred)
            new_rule.predicates.append(predicate)

            # Introduce new variable
            new_rule.shared_var[predicate.output_var] = [predicate]
            new_rule.shared_var[predicate.input_var].append(predicate)
            new_rule.latest_var = predicate.output_var

        new_rule.__refresh_coverage()
        new_rule.__refresh_statistics()
        return new_rule

    def _replace_predicate(self, target, replacement):
        '''
        Replaces 'target' with 'replacement' in the rule.
        '''
        Rule.__replace(self.predicates, target, replacement)
        self.covered_examples = self.covered_examples & \
            replacement.domain[replacement.input_var]

        # Reference possible consumers
        replacement.consumer_predicate = target.consumer_predicate

        # Update the backlinks
        if replacement.producer_predicate:
            replacement.producer_predicate.consumer_predicate = replacement
        if replacement.consumer_predicate:
            replacement.consumer_predicate.producer_predicate = replacement

        # Update the shared var list
        shared_list = self.shared_var[target.input_var]
        Rule.__replace(shared_list, target, replacement)

        # Recalc the covered examples and statistics
        self.__refresh_coverage()
        self.__refresh_statistics()

    @staticmethod
    def __replace(l, target, replacement):
        idx = l.index(target)
        l[idx] = replacement

    def __refresh_coverage(self):
        '''
        Recalculates the covered examples.
        '''
        var = self.shared_var[self.head_var]
        self.covered_examples = self.__covered_examples(var)

    def __covered_examples(self, predicates):
        '''
        Recursively calculates the covered examples for a given set of
        predicates that share a variable.
        '''
        covered_examples = self.kb.get_full_domain()
        for pred in predicates:
            if isinstance(pred, BinaryPredicate):

                # Predicates that share the new variable, without 'pred'
                shared = self.shared_var[pred.output_var][:]
                shared.remove(pred)
                existential_cov_examples = self.__covered_examples(shared)
                reverse_members = self.kb.get_reverse_members(pred.label)
                tmp_covered = self.kb.get_empty_domain()

                # Calculate all examples that have a pair for this relation
                for idx in self.kb.bits_to_indices(existential_cov_examples):
                    if reverse_members.has_key(idx):
                        tmp_covered |= reverse_members[idx]
                covered_examples &= tmp_covered
            else:
                covered_examples &= pred.domain[pred.input_var]
        return covered_examples

    def __refresh_statistics(self):
        '''
        Recalculates the statistics for this rule.
        '''
        self.coverage = self.covered_examples.count()

        indices = self.kb.bits_to_indices(self.covered_examples)
        ex_scores = [self.kb.get_score(idx) for idx in indices]

        if self.target_type == Example.Ranked:
            self.mean = avg(ex_scores)
            self.sd = std(ex_scores)
            self.score = self.kb.score_fun(self)
        else:
            self.distribution = defaultdict(int)
            for score in ex_scores:
                self.distribution[score] += 1
            self.score = self.kb.score_fun(self)

    def similarity(self, rule):
        '''
        Calculates the similarity between this rule and 'rule'.
        '''
        intersection = self.covered_examples & rule.covered_examples
        return intersection.count()/float(max(self.coverage, rule.coverage))

    def size(self):
        '''
        Returns the number of conjunts.
        '''
        return len(self.predicates)

    def examples(self):
        '''
        Returns the covered examples.
        '''
        indices = self.kb.bits_to_indices(self.covered_examples)
        return [self.kb.examples[idx] for idx in indices]

    def rule_report(self, show_uris=False):
        '''
        Rule as string with some statistics.
        '''
        conjuncts = []
        for pred in self.predicates:

            label = pred.label
            if '#' in label and show_uris:
                label = pred.label.split('#')[-1]

            if isinstance(pred, UnaryPredicate):
                if pred.negated:
                    label = '~' + label
                conj = '%s(%s)' % (label, pred.input_var)
            else:
                conj = '%s(%s, %s)' % (label,
                                       pred.input_var,
                                       pred.output_var)
            conjuncts.append(conj)

        s = ', '.join(conjuncts)

        if self.target_type == Example.ClassLabeled:

            accuracy = self.distribution[self.target] / float(self.coverage)
            stats = (self.coverage,
                     self.distribution[self.target],
                     accuracy,
                     self.kb.score_fun.__name__,
                     self.score,
                     self.pval)
            s += ' [cov=%d, pos=%d, prec=%.3f, %s=%.3f, pval=%.3f]' % stats

        else:
            s += ' [size=%d, score=%.3f]' % (self.coverage, self.score)

        return s

    def __str__(self):
        return self.rule_report(show_uris=True)

    @staticmethod
    def ruleset_report(rules, show_uris=False):
        target, var = rules[0].target, rules[0].head_var
        head = '\'%s\'(%s) <--\n\t' % (target, var)

        ruleset = []
        for rule in sorted(rules, key=lambda r: r.score, reverse=True):
            rule = str(rule)
            rule = rule if show_uris else rule.split('#')[-1]
            ruleset.append(rule)

        return head + '\n\t'.join(ruleset)
