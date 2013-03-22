'''
Created on Jul 19, 2012

@author: anzev
'''
from collections import defaultdict
from bitarray import bitarray
from rdflib import RDF, RDFS, Namespace, URIRef
import numpy as np
import os

class Example:
    '''
    Represents an example with its score, label, id and annotations.
    '''
    ClassLabeled = 'class'
    Ranked = 'ranked'
    def __init__(self, id, label, score, annotations=[], weights={}):
        self.id = id
        self.label = label
        self.score = score
        if not type(score) in [str, unicode]:
            self.target_type = Example.Ranked
        else:
            self.target_type = Example.ClassLabeled
        self.annotations = annotations
        self.weights = weights
        
    def __str__(self):
        if self.score_type == ScoreTypeRanked:
            return '<id=%d, score=%.5f, label=%s>' % (self.id, self.score, self.label)
        else:
            return '<id=%d, class=%s, label=%s>' % (self.id, self.score, self.label)
    
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
                
        self.head_var = self.predicates[0].input_var if self.predicates else None
        self.shared_var = { self.head_var : self.predicates }  # Dictionary of predicates that share a certain variable
        
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
        
    def clone(self):
        '''
        Returns a clone of this rule. The predicates themselves are NOT cloned.
        '''
        new_rule = Rule(self.kb)
        new_rule.predicates = self.predicates[:]
        new_rule.covered_examples = self.covered_examples
        new_rule.latest_var = self.latest_var
        new_rule.head_var = self.head_var
        new_rule.shared_var = {}
        new_rule.target = self.target
        for var in self.shared_var:
            new_rule.shared_var[var] = self.shared_var[var][:]
        return new_rule 
    
    def clone_swap_with_subclass(self, target_pred, child_pred_label):
        '''
        Returns a copy of this rule where 'target_pred' is swapped for 'child_pred_label'.
        '''
        new_rule = self.clone()
                
        # Create the instance of the child pred 
        child_pred = UnaryPredicate(child_pred_label, self.kb.get_members(child_pred_label), self.kb, producer_pred=target_pred.producer_predicate, custom_var_name=target_pred.input_var)
        
        Rule.__replace(new_rule.predicates, target_pred, child_pred)
        new_rule.covered_examples = self.covered_examples & child_pred.domain[child_pred.input_var]
        
        # Reference possible consumers
        child_pred.consumer_predicate = target_pred.consumer_predicate
        
        # Update the backlinks
        if child_pred.producer_predicate:
            child_pred.producer_predicate.consumer_predicate = child_pred
        if child_pred.consumer_predicate: 
            child_pred.consumer_predicate.producer_predicate = child_pred
            
        # Update the shared var list
        shared_list = new_rule.shared_var[target_pred.input_var]
        Rule.__replace(shared_list, target_pred, child_pred)
        
        # Recalc the covered examples and statistics
        new_rule.__refresh_coverage()
        new_rule.__refresh_statistics()
               
        return new_rule
    
    def clone_append(self, predicate_label, producer_pred, bin=False):
        '''
        Returns a copy of this rule where 'predicate_label' is appended to the rule.
        '''
        if not bin:
            new_rule = self.clone()
            predicate = UnaryPredicate(predicate_label, self.kb.get_members(predicate_label), self.kb, producer_pred=producer_pred)
            new_rule.predicates.append(predicate)
            new_rule.shared_var[producer_pred.output_var].append(predicate)
            #new_rule.covered_examples = self.covered_examples & predicate.domain[predicate.input_var]
        else:
            new_rule = self.clone()
            predicate = BinaryPredicate(predicate_label, self.kb.get_members(predicate_label), self.kb, producer_pred=producer_pred)
            new_rule.predicates.append(predicate)
            # Introduce new variable
            new_rule.shared_var[predicate.output_var] = [predicate]
            new_rule.shared_var[predicate.input_var].append(predicate)
            new_rule.latest_var = predicate.output_var
            
        new_rule.__refresh_coverage()
        new_rule.__refresh_statistics()
        return new_rule
    
    @staticmethod
    def __replace(l, target, replacement):
        idx = l.index(target)
        l[idx] = replacement
    
    def __refresh_coverage(self):
        '''
        Recalculates the covered examples.
        '''
        self.covered_examples = self.__covered_examples(self.shared_var[self.head_var])
    
    def __covered_examples(self, predicates):
        '''
        Recursively calculates the covered examples for a given set of predicates that share a variable.
        '''
        covered_examples = self.kb.get_full_domain()
        for pred in predicates:
            if isinstance(pred, BinaryPredicate):
                shared = self.shared_var[pred.output_var][:]
                shared.remove(pred)     # predicates that share the new variable, without 'pred'
                existential_covered_examples = self.__covered_examples(shared)
                reverse_members = self.kb.get_reverse_members(pred.label)
                tmp_covered = self.kb.get_empty_domain()
                # Calculate all examples that have a pair for this relation
                for idx in self.kb.bits_to_indices(existential_covered_examples):
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
        ex_scores = [self.kb.get_score(idx) for idx in self.kb.bits_to_indices(self.covered_examples)]
        if self.target_type == Example.Ranked:
            self.mean = np.average(ex_scores)
            self.sd = np.std(ex_scores)
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
        #descr_int = set([pred.label for pred in self.predicates]).intersection(set([pred.label for pred in rule.predicates]))   # Similarity of the descriptions
        #return 0.9 * intersection.count() / float(max(self.coverage, rule.coverage)) + 0.1 * len(descr_int) / float(max(len(self.predicates), len(rule.predicates)))
        return intersection.count() / float(max(self.coverage, rule.coverage))
    
    def size(self):
        '''
        Returns the number of conjunts.
        '''
        return len(self.predicates)
    
    def examples(self):
        '''
        Returns the covered examples.
        '''
        return [self.kb.examples[idx] for idx in self.kb.bits_to_indices(self.covered_examples)]
    
    def __str__(self):
        conjuncts = []
        for pred in self.predicates:
            if isinstance(pred, UnaryPredicate):
                conj = '%s(%s)' % (pred.label, pred.input_var)
            else:
                conj = '%s(%s, %s)' % (pred.label, pred.input_var, pred.output_var) 
            conjuncts.append(conj)
        s = ', '.join(conjuncts)
        s += ' [size = %d, score = %.3f]' % (self.coverage, self.score)
        return s

class Predicate:
    '''
    Represents a predicate as a member of a certain rule.
    '''
    i = -1
    def __init__(self, label, kb, producer_pred):
        self.label = label
        self.kb = kb
        self.producer_predicate = producer_pred  # Whose predicate's out var this predicate consumes
        if self.producer_predicate:
            producer_pred.consumer_predicate = self
        self.consumer_predicate = None  # Which predicate consumes this predicate's out var
        
    @staticmethod
    def _avar():
        '''
        Anonymous var name generator.
        '''
        Predicate.i = Predicate.i + 1
        return 'X%d' % Predicate.i

class UnaryPredicate(Predicate):
    '''
    A unary predicate.
    '''
    def __init__(self, label, members, kb, producer_pred=None, custom_var_name=None):
        Predicate.__init__(self, label, kb, producer_pred)
        if not producer_pred:
            self.input_var = Predicate._avar() if not custom_var_name else custom_var_name
        else:
            self.input_var = producer_pred.output_var
        self.output_var = self.input_var
        self.domain = {self.input_var : members}

class BinaryPredicate(Predicate):
    '''
    A binary predicate.
    '''
    def __init__(self, label, pairs, kb, producer_pred=None):
        '''
        The predicate's name and the tuples satisfying it.
        '''
        Predicate.__init__(self, label, kb, producer_pred)
        # The input var should match with the producers output var
        self.input_var = Predicate._avar() if not producer_pred else producer_pred.output_var
        self.output_var = Predicate._avar()
        if producer_pred:
            potential_inputs = self.producer_predicate.domain[self.producer_predicate.output_var]
            # Find which inputs have pairs
            inputs = potential_inputs & kb.get_domains(label)[0]
            outputs = kb.get_empty_domain()
            for el1 in kb.bits_to_indices(inputs):
                outputs |= pairs[el1]
        else:  # No producer predicate.
            inputs, outputs = kb.get_domains(label)
        self.domain = {self.input_var : inputs, self.output_var : outputs}

class ExperimentKB:
    '''
    The knowledge base for one specific experiment.
    '''
    def __init__(self, triplets, score_fun, user_namespaces=[], instances_as_leaves=True):
        '''
        Initialize the knowledge base with the given triplet graph. The target class is given with 'target_class' - this is the class to be described in the induction step.
        '''
        self.g = triplets
        self.user_namespaces = user_namespaces
        self.score_fun = score_fun
        self.sub_class_of = defaultdict(list)
        self.super_class_of = defaultdict(list)
        self.predicates = set()
        self.binary_predicates = set()
        self.class_values = set()
        
        # Parse the examples schema
        self.g.parse(os.path.join(os.path.dirname(__file__), 'examples.n3'), format='n3')
        FIRST = Namespace('http://project-first.eu/ontology#')
        
        # Extract the available examples from the graph
        self.examples_uris = [ex for ex in self.g.subjects(predicate=RDF.type, object=FIRST.Example)]
        self.uri_to_idx = {}
        examples = []
        for i, ex_uri in enumerate(self.examples_uris):
            annotation_links = [annot for annot in self.g.objects(subject=ex_uri, predicate=FIRST.annotated_with)]
            annotations = []
            weights = {}
            for link in annotation_links:
                annotation = [str(one) for one in self.g.objects(subject=link, predicate=FIRST.annotation)][0]
                weights_list = [one for one in self.g.objects(subject=link, predicate=FIRST.weight)]
                if weights_list:
                    weights[annotation] = float(weights_list[0])
                annotations.append(annotation)
            score_list = list(self.g.objects(subject=ex_uri, predicate=FIRST.score))
            if score_list:
                score = float(score_list[0])
            else:
                score_list = list(self.g.objects(subject=ex_uri, predicate=FIRST.class_label))
                score = str(score_list[0])
                self.class_values.add(score)
            self.uri_to_idx[ex_uri] = i
            examples.append(Example(i, str(ex_uri), score, annotations=annotations, weights=weights))
        self.examples = examples

        # Ranked or class-labeled data
        self.target_type = self.examples[0].target_type

        if not self.examples:
            raise Exception("No examples provided!")
        
        # Get the subClassOf hierarchy
        for sub, obj in self.g.subject_objects(predicate=RDFS.subClassOf):
            if self.user_defined(sub) and self.user_defined(obj):
                self.add_sub_class(sub, obj)
        
        # Include the instances as predicates as well
        if instances_as_leaves:
            for sub, obj in self.g.subject_objects(predicate=RDF.type):
                if self.user_defined(sub) and self.user_defined(obj):
                    self.add_sub_class(sub, obj)
        
        # Find the user-defined object predicates defined between examples
        for pred in set(self.g.subjects(predicate=RDFS.domain, object=FIRST.Example)) \
                        .intersection(self.g.subjects(predicate=RDFS.range, object=FIRST.Example)):
            if self.user_defined(pred):
                self.binary_predicates.add(str(pred))
        
        # Calculate the members for each predicate
        self.members = defaultdict(set)
        for ex in examples:
            for inst in ex.annotations:
                if instances_as_leaves:
                    self.members[inst].add(ex.id)
                else:
                    for obj in self.g.objects(subject=URIRef(inst), predicate=RDF.type):
                        self.members[str(obj)].add(ex.id)

        # Find the root classes
        roots = filter(lambda pred: self.sub_class_of[pred] == [], self.super_class_of.keys())
       
        # Add a dummy root
        self.dummy_root = 'root'
        self.predicates.add(self.dummy_root)
        for root in roots:
            self.add_sub_class(root, self.dummy_root)
        
        self.sub_class_of_closure = defaultdict(set)
        for pred in self.super_class_of.keys():
            self.sub_class_of_closure[pred].update(self.sub_class_of[pred])
        
        # Calc the closure to get the members of the subClassOf hierarchy
        def closure(pred, lvl):
            children = self.super_class_of[pred]
            self.levels[lvl].add(pred)
            if children:
                mems = set()
                for child in children: 
                    self.sub_class_of_closure[child].update(self.sub_class_of_closure[pred])
                    mems.update(closure(child, lvl + 1))
                self.members[pred] = mems
                return mems
            else:
                return self.members[pred]

        # Level-wise predicates
        self.levels = defaultdict(set)
        
        # Run the closure from root
        closure(self.dummy_root, 0)
               
        # Members of non-unary predicates
        self.binary_members = defaultdict(dict)
        self.reverse_binary_members = defaultdict(dict)
        for pred in self.binary_predicates:
            pairs = self.g.subject_objects(predicate=URIRef(pred))
            for pair in pairs:
                el1, el2 = self.uri_to_idx[pair[0]], self.uri_to_idx[pair[1]]
                if self.binary_members[pred].has_key(el1):
                    self.binary_members[pred][el1].append(el2)
                else:
                    self.binary_members[pred][el1] = [el2]
                
                # Add the reverse as well
                if self.reverse_binary_members[pred].has_key(el2):
                    self.reverse_binary_members[pred][el2].append(el1)
                else:
                    self.reverse_binary_members[pred][el2] = [el1]
        
        # Bitset of examples for input and output 
        self.binary_domains = {}
        for pred in self.binary_predicates:
            self.binary_domains[pred] = (
                self.indices_to_bits(self.binary_members[pred].keys()), 
                self.indices_to_bits(self.reverse_binary_members[pred].keys())
            )
        
        # Calc the corresponding bitsets
        self.bit_members = {}
        for pred in self.members.keys():
            self.bit_members[pred] = self.indices_to_bits(self.members[pred])
              
        self.bit_binary_members = defaultdict(dict)
        self.reverse_bit_binary_members = defaultdict(dict)
        for pred in self.binary_members.keys():
            for el in self.binary_members[pred].keys():
                self.bit_binary_members[pred][el] = self.indices_to_bits(self.binary_members[pred][el])
            for el in self.reverse_binary_members[pred].keys():
                self.reverse_bit_binary_members[pred][el] = self.indices_to_bits(self.reverse_binary_members[pred][el])
        
        # Statistics
        if self.target_type == Example.Ranked:
            self.mean = np.average([ex.score for ex in self.examples])
            self.sd = np.std([ex.score for ex in self.examples])
        else:
            self.distribution = defaultdict(int)
            for ex in self.examples:
                self.distribution[ex.score] += 1

        # def print_hierarchy(root, d=0):
        #     print '%s%s' % ('\t'*d, root.encode('ascii', 'ignore'))
        #     for subclass in self.super_class_of[root]:
        #         print_hierarchy(subclass, d=d+1)
        # print
        # print_hierarchy(self.dummy_root)

    def user_defined(self, uri):
        '''
        Is this resource user defined?
        '''
        return any([uri.startswith(ns) for ns in self.user_namespaces]) if self.user_namespaces else True
        
    def add_sub_class(self, sub, obj):
        '''
        Adds the resource 'sub' as a subclass of 'obj'.
        '''
        sub, obj = unicode(sub).encode('ascii', 'ignore'), unicode(obj).encode('ascii', 'ignore')
        self.predicates.update([sub, obj])
        self.sub_class_of[sub].append(obj)
        self.super_class_of[obj].append(sub)

    def super_classes(self, pred):
        '''
        Returns all super classes of pred (with transitivity).
        '''
        return self.sub_class_of_closure[pred]
    
    def get_root(self):
        '''
        Root predicate, which covers all examples.
        '''
        return UnaryPredicate(self.dummy_root, self.get_full_domain(), self, custom_var_name='X')
            
    def get_subclasses(self, predicate, producer_pred=None):
        '''
        Returns a list of subclasses (as predicate objects) for 'predicate'.
        '''
        #return [UnaryPredicate(pred_label, self.bit_members[pred_label], self, producer_pred) for pred_label in self.super_class_of[predicate.label]]
        return self.super_class_of[predicate.label]
        
    def get_members(self, predicate, bit=True):
        '''
        Returns the examples for this predicate, either as a bitset or a set of ids.
        '''
        if predicate in self.predicates:
            return self.bit_members[predicate] if bit else self.members[predicate]
        else:
            return self.bit_binary_members[predicate] if bit else self.binary_members[predicate]
        
    def get_reverse_members(self, predicate, bit=True):
        '''
        Returns the examples for this predicate, either as a bitset or a set of ids.
        '''
        return self.reverse_bit_binary_members[predicate] if bit else self.reverse_binary_members[predicate]
    
    def get_domains(self, predicate):
        '''
        Returns the bitsets for input and outputexamples of the binary predicate 'predicate'.
        '''
        return self.binary_domains[predicate]
    
    def get_examples(self):
        '''
        Returns all examples for this experiment.
        '''
        return self.examples
    
    def n_examples(self):
        '''
        Returns the number of examples.
        '''
        return len(self.examples)
    
    def get_full_domain(self):
        '''
        Returns a bitset covering all examples.
        '''
        return bitarray([True] * self.n_examples())
    
    def get_empty_domain(self):
        '''
        Returns a bitset covering no examples.
        '''
        return bitarray([False] * self.n_examples())
    
    def get_score(self, ex_idx):
        '''
        Returns the score for example id 'ex_idx'.
        '''
        return self.examples[ex_idx].score
    
    def bits_to_indices(self, bits):
        '''
        Converts the bitset to a set of indices.
        '''
        return bits.search(bitarray([1]))

    def indices_to_bits(self, indices):
        '''
        Converts the indices to a bitset.
        '''
        bits = self.get_empty_domain()
        for idx in indices:
            bits[idx] = True
        return bits
    