'''
Created on Jul 24, 2012

@author: anzev
'''
from math import sqrt
from core import *

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
        if rule.coverage == rule.kb.n_examples(): # The enrichment score of a rule covering all examples is 1
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

class Learner:
    '''
    Learner class, supporting various types of induction from the knowledge base.
    
    TODO: Bottom clause?
    '''
    Similarity = 'similarity'
    Improvement = 'improvement'
    Default = 'default'
    def __init__(self, kb, n=None, min_sup=1, sim=1):
        self.kb = kb
        self.n = n      # Beam length
        self.min_sup = min_sup
        self.sim = sim
        self.extending = Learner.Similarity
    
    def induce_beam(self):
        '''
        Induces rules for the given knowledge base using beam search.
        '''
        root_pred = self.kb.get_root()
        rules = [Rule(self.kb, predicates=[root_pred])]
        while True:
            old_score = self.group_score(rules)
            new_rules = rules[:]
            for rule in rules:
                self.extend(new_rules, self.specialize_naive(rule))
            # Take the first N rules
            rules = sorted(new_rules, key=lambda rule: rule.score, reverse=True)[:self.n]
            new_score = self.group_score(rules)
            if 1 - abs(old_score/new_score) < 0.001:
                break
        return rules
    
    def induce(self):
        '''
        Induces rules for the given knowledge base.
        '''
        root_pred = self.kb.get_root()
        rules = [Rule(self.kb, predicates=[root_pred])]
        rules = self.__induce_level(rules)
        return rules
    
    def __induce_level(self, rules):
        '''
        Specializes the rules for the last level with unary predicates.
        '''
        while True:
            old_score = self.group_score(rules)
            new_rules = rules[:]
            for rule in rules:
                specializations = self.specialize(rule)
#                for spec_rule in specializations:
#                    if rule.similarity(spec_rule) == 1.0:
#                        idx = new_rules.index(rule)
#                        new_rules[idx] = spec_rule
#                        break
                self.extend(new_rules, specializations)
            # Take the first N rules
            rules = sorted(new_rules, key=lambda rule: rule.score, reverse=True)[:self.n]
            new_score = self.group_score(rules)
            #if not improved_level: #abs(new_score - old_score) < 1e-5:
            if 1 - abs(old_score/new_score) < 0.01:
                break
        return new_rules
    
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
        Extends the list based on how similar is 'new_rule' to the rules contained in 'rules'.
        '''
        for new_rule in specializations:
            similar = False
            tmp_rules = rules[:]
            for rule in tmp_rules:
                sim = rule.similarity(new_rule)
                if sim >= self.sim:
#                    if sim == self.sim:
#                        # If they are exactly the same, prefer the more specific description
#                        idx = rules.index(rule)
#                        rules[idx] = new_rule
#                        break
#                    else:
#                        similar = True
#                        break
                    similar = True
                    break
            if not similar:
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
        # Swapping unary predicates with subclasses, swap only the predicates with the latest variable
        for pred in filter(lambda p: isinstance(p, UnaryPredicate), eligible_preds):
            for sub_class in self.kb.get_subclasses(pred):
                new_rule = rule.clone_swap_with_subclass(pred, sub_class)
                if self.good_enough(new_rule):
                    specializations.append(new_rule)
        # Append new root            
        specializations.append(rule.clone_append(self.kb.dummy_root, producer_pred=rule.predicates[-1]))
        return specializations
    
    def specialize(self, rule):
        '''
        Returns a list of all specializations of 'rule'.
        '''
        specializations = []
        eligible_preds = rule.shared_var[rule.latest_var]
        # Swapping unary predicates with subclasses, swap only the predicates with the latest variable
        for pred in filter(lambda p: isinstance(p, UnaryPredicate), eligible_preds):
            for sub_class in self.kb.get_subclasses(pred):
                new_rule = rule.clone_swap_with_subclass(pred, sub_class)
                if self.good_enough(new_rule):
                    specializations.append(new_rule)
        # This makes sure we are not specializing a default rule by appending, 
        # this rule should instead be reached by the specialization step above.
        if not (len(eligible_preds) == 1 and eligible_preds[0].label == self.kb.get_root().label):    
            # Calculate the union of superclasses of each predicate
            supers = set()
            for pred in eligible_preds:
                supers.update(self.kb.super_classes(pred.label))
                supers.add(pred)
            # Calculate the top-most left-most non-ancestor
            for lvl in sorted(self.kb.levels.keys()):
                level = self.kb.levels[lvl]
                diff = level.difference(supers)
                if diff:
                    # The next predicate to specialize with is the left-most
                    for pred in sorted(list(diff)): 
                        # Appending a new predicate, the last predicate is always the producer
                        new_rule = rule.clone_append(pred, producer_pred=rule.predicates[-1])
                        if self.good_enough(new_rule):
                            specializations.append(new_rule)
                            break
        # Introduce new binary relation
        if isinstance(rule.predicates[-1], UnaryPredicate):
            specializations.extend(self.specialize_add_relation(rule))
        return specializations
    
    def specialize_add_relation(self, rule):
        '''
        Specialize with new binary relation.
        '''
        specializations = []
        #if rule.size() == 5:  # Max size reached
        #    return specializations
        for pred in self.kb.binary_predicates:
            new_rule = rule.clone_append(pred, producer_pred=rule.predicates[-1], bin=True)
            if self.good_enough(new_rule):
                specializations.append(new_rule)
        return specializations
    
    def good_enough(self, rule):
        '''
        Is the rule good enough to be further refined?
        '''
        return rule.coverage >= self.min_sup
    
    def group_score(self, rules):
        '''
        Calculates the score of the whole list of rules.
        '''
        return sum([rule.score for rule in rules])
    