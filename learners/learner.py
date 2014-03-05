'''
Main learner class.

@author: anze.vavpetic@ijs.si
'''
from collections import defaultdict

from core import UnaryPredicate, Rule, Example
from core.settings import logger
from stats.significance import is_redundant
from stats.scorefunctions import interesting

class Learner:
    '''
    Learner class, supporting various types of induction
    from the knowledge base.

    TODO:
        - bottom clause approach
        - feature construction
    '''
    Similarity = 'similarity'
    Improvement = 'improvement'
    Default = 'default'

    def __init__(self, kb, n=None, min_sup=1, sim=1, depth=4, target=None,
                 use_negations=False):
        self.kb = kb
        self.n = n          # Beam length
        self.min_sup = min_sup
        self.sim = sim
        self.extending = Learner.Similarity
        self.depth = depth  # Max number of conjunctions
        self.use_negations = use_negations

        if kb.is_discrete_target():
            self.target = list(self.kb.class_values)[0] if not target else target
        else:
            self.target = None

        self.pruned_subclasses = self.calc_pruned_subclasses()
        self.pruned_superclasses_closure = self.calc_pruned_superclasses()

    def calc_pruned_subclasses(self):
        n_mems = lambda pred: self.kb.get_members(pred).count()
        min_sup = lambda pred: n_mems(pred) >= self.min_sup
        pruned_subclasses = {}
        for pred in self.kb.predicates:
            subclasses = self.kb.get_subclasses(pred)
            pruned_subclasses[pred] = filter(min_sup, subclasses)

        return pruned_subclasses

    def calc_pruned_superclasses(self):
        n_mems = lambda pred: self.kb.get_members(pred).count()
        min_sup = lambda pred: n_mems(pred) >= self.min_sup
        pruned_superclasses = {}
        for pred in self.kb.predicates:
            superclasses = self.kb.super_classes(pred)
            pruned_superclasses[pred] = filter(min_sup, superclasses)
        
        return pruned_superclasses

    def get_subclasses(self, pred):
        return self.pruned_subclasses[pred.label]

    def get_superclasses(self, pred):
        return self.pruned_superclasses_closure[pred]

    def induce_beam(self):
        '''
        Induces rules for the given knowledge base using beam search.
        '''
        root_pred = self.kb.get_root()
        rules = [Rule(self.kb, predicates=[root_pred], target=self.target)]
        while True:
            old_score = self.group_score(rules)
            new_rules = rules[:]
            for rule in rules:
                self.extend(new_rules, self.specialize_naive(rule))

            # Take the first N rules
            rules = sorted(new_rules,
                           key=lambda rule: rule.score, reverse=True)[:self.n]
            new_score = self.group_score(rules)
            if 1 - abs(old_score/new_score) < 0.001:
                break
        return rules

    def induce(self):
        '''
        Induces rules for the given knowledge base.
        '''
        root_pred = self.kb.get_root()
        rules = [Rule(self.kb, predicates=[root_pred], target=self.target)]
        rules = self.__induce_level(rules)
        return filter(interesting, rules)

    def __induce_level(self, rules):
        '''
        Specializes the rules for the last level with unary predicates.
        '''
        while True:
            old_score = self.group_score(rules)
            new_rules = rules[:]
            for i, rule in enumerate(rules):
                specializations = self.specialize(rule)
                self.extend(new_rules, specializations)

            # Take the first N rules
            rules = sorted(new_rules,
                           key=lambda rule: rule.score,
                           reverse=True)[:self.n]

            new_score = self.group_score(rules)

            logger.debug("Old score: %.3f, New score: %.3f" % (old_score, new_score))

            if 1 - abs(old_score/(new_score+0.0001)) < 0.01:
                break

        return rules

    def extend(self, rules, specializations):
        '''
        Extends the ruleset in the given way.
        '''
        if self.extending == Learner.Default:
            return rules.extend(specializations)
        elif self.extending == Learner.Improvement:
            return self.extend_replace_worst(rules, specializations)
        elif self.extending == Learner.Similarity:
            return self.extend_with_similarity(rules, specializations)

    def extend_with_similarity(self, rules, specializations):
        '''
        Extends the list based on how similar is 'new_rule'
        to the rules contained in 'rules'.
        '''
        for new_rule in specializations:
            tmp_rules = rules[:]
            for rule in tmp_rules:
                sim = rule.similarity(new_rule)
                if sim >= self.sim and len(rules) > 0.5*self.n:
                    break
            else:
                rules.append(new_rule)

    def extend_replace_worst(self, rules, specializations):
        '''
        Extends the list by replacing the worst rules.
        '''
        improved = False
        for new_rule in sorted(specializations, key=lambda rule: rule.score):
            worst = min(rules, key=lambda rule: rule.score)
            if new_rule.score > worst:
                Rule.__replace(rules, worst, new_rule)
                improved = True
        return improved

    def specialize_naive(self, rule):
        '''
        Returns a list of all specializations of 'rule'.
        '''
        specializations = []
        eligible_preds = rule.shared_var[rule.latest_var]
        is_unary = lambda p: isinstance(p, UnaryPredicate)

        # Swapping unary predicates with subclasses, swap only the predicates
        # with the latest variable
        for pred in filter(is_unary, eligible_preds):
            for sub_class in self.get_subclasses(pred):
                new_rule = rule.clone_swap_with_subclass(pred, sub_class)
                if self.can_specialize(new_rule):
                    specializations.append(new_rule)

        # Append new root
        new_rule = rule.clone_append(self.kb.dummy_root,
                                     producer_pred=rule.predicates[-1])
        specializations.append(new_rule)
        return specializations

    def specialize(self, rule):
        '''
        Returns a list of all specializations of 'rule'.
        '''
        logger.debug('Specializing rule: %s' % rule)
        specializations = []
        eligible_preds = rule.shared_var[rule.latest_var]
        is_unary = lambda p: isinstance(p, UnaryPredicate)

        # Swapping unary predicates with subclasses, swap only
        # the predicates with the latest variable
        for pred in filter(is_unary, eligible_preds):
            logger.debug('Predicate to swap: %s' % pred.label)
            for sub_class in self.get_subclasses(pred):
                logger.debug('Swapping with %s' % sub_class)
                new_rule = rule.clone_swap_with_subclass(pred, sub_class)
                if self.can_specialize(new_rule):
                    specializations.append(new_rule)

        if self.use_negations:
            # Negate the last predicate
            for pred in filter(is_unary, eligible_preds):
                logger.debug('Predicate to negate: %s' % pred.label)
                new_rule = rule.clone_negate(pred)
                if self.can_specialize(new_rule):
                    specializations.append(new_rule)

        # This makes sure we are not specializing a default rule by appending,
        # this rule should instead be reached by the specialization step above.
        if not (len(eligible_preds) == 1 and
           eligible_preds[0].label == self.kb.get_root().label):

            # Calculate the union of superclasses of each predicate
            supers = set()
            for pred in eligible_preds:
                supers.update(self.get_superclasses(pred.label))
                supers.add(pred)

            # Calculate the top-most left-most non-ancestor
            for lvl in sorted(self.kb.levels.keys()):

                level = self.kb.levels[lvl]
                diff = level.difference(supers)
                if diff:

                    # The next predicate to specialize with is the left-most
                    for pred in sorted(list(diff)):

                        # Appending a new predicate, the last predicate
                        # is always the producer
                        last_pred = rule.predicates[-1]
                        new_rule = rule.clone_append(pred,
                                                     producer_pred=last_pred)
                        if self.can_specialize(new_rule) and \
                           self.non_redundant(rule, new_rule):
                            specializations.append(new_rule)
                            break

        # Introduce new binary relation
        if isinstance(rule.predicates[-1], UnaryPredicate):
            specializations.extend(self.specialize_add_relation(rule))

        logger.debug('All specializations %s'
                     % [str(rule) for rule in specializations])

        return specializations

    def specialize_add_relation(self, rule):
        '''
        Specialize with new binary relation.
        '''
        specializations = []
        for pred in self.kb.binary_predicates:

            last_pred = rule.predicates[-1]
            new_rule = rule.clone_append(pred, producer_pred=last_pred,
                                         bin=True)

            if self.can_specialize(new_rule):
                specializations.append(new_rule)
        return specializations

    def can_specialize(self, rule):
        '''
        Is the rule good enough to be further refined?
        '''
        return rule.coverage >= self.min_sup and rule.size() <= self.depth

    def non_redundant(self, rule, new_rule):
        '''
        Is the rule non-redundant compared to its immediate generalization?
        '''
        if rule.target_type == Example.Ranked:
            return True
        else:
            return not is_redundant(rule, new_rule)

    def group_score(self, rules):
        '''
        Calculates the score of the whole list of rules.
        '''
        return sum([rule.score for rule in rules])
