'''
Storing results.

@author: anze.vavpetic@ijs.si
'''
import json
import uuid
from hedwig.core.settings import VERSION, DESCRIPTION
from hedwig.core.predicate import UnaryPredicate
from hedwig.core.settings import DEFAULT_ANNOTATION_NAME


def parameters_report(args, start, time_taken):
    sep = '-'*40 + '\n'
    rep = DESCRIPTION + '\n' +\
        'Version: %s' % VERSION + '\n' +\
        'Start: %s' % start + '\n' +\
        'Time taken: %.2f seconds' % time_taken + '\n' +\
        'Parameters:' + '\n'

    rep += arguments_report(args)
    rep = sep + rep + sep
    return rep


def arguments_report(args, single_line=False):
    arg_list = []
    for arg, val in args.items():
        arg_str = '%s=%s' % (arg, str(val))
        arg_list.append(arg_str)
    if single_line:
        s = ', '.join(arg_list)
    else:
        s = ''.join(map(lambda arg: '\t{}\n'.format(arg), arg_list))
    return s


def generate_rules_report(kwargs, rules_per_target,
                          human=lambda label, rule: label):
    rules_report = ''
    for _, rules in rules_per_target:
        if rules:
            rules_report += ruleset_report(rules, show_uris=kwargs['uris'],
                                                human=human)
            rules_report += '\n'
    if not rules_report:
        rules_report = 'No significant rules found'
    return rules_report


def ruleset_report(rules, show_uris=False, latex=False,
                   human=lambda label, rule: label):
    if latex:
        return _latex_ruleset_report(rules)
    else:
        return _plain_ruleset_report(rules, show_uris=show_uris,
                                          human=human)


def latex_ruleset_report(rules):
    target, var = rules[0].target, rules[0].head_var
    if target:
        head = '%s(%s) $\leftarrow$ ' % (target, var)
    else:
        head = ''

    _tex_report = \
        r'\begin{tabular}{clccccc}\hline' + '\n' \
        r'\textbf{\#} & \textbf{Rule} & \textbf{TP} & \textbf{FP} & \textbf{Precision} & \textbf{Lift} & \textbf{p-value}\\\hline' + '\n'

    for i, rule in enumerate(sorted(rules, key=lambda r: r.score, reverse=True)):
        rule_report = rule._latex_report()
        stats = (i+1,
                 head + rule_report,
                 rule.distribution[rule.target],
                 rule.coverage - rule.distribution[rule.target],
                 rule.distribution[rule.target]/float(rule.coverage),
                 rule.score,
                 rule.pval)
        _tex_report += r'%d & \texttt{%s} & %d & %d & %.2f & %.2f & %.3f\\' % stats
        _tex_report += '\n'

    _tex_report += \
        r'\hline' + '\n' \
        r'\end{tabular}' + '\n'

    return _tex_report


def _plain_ruleset_report(rules, show_uris=False,
                          human=lambda label, rule: label):

    target, var = rules[0].target, rules[0].head_var
    if target:
        head = '\'%s\'(%s) <--\n\t' % (target, var)
    else:
        head = ''

    ruleset = []
    for rule in sorted(rules, key=lambda r: r.score, reverse=True):
        rule = rule._plain_report(show_uris=show_uris, human=human)
        ruleset.append(rule)

    return head + '\n\t'.join(ruleset)


def ruleset_examples_json(rules_per_target, show_uris=False):
    examples_output = []
    for target_class, rules in rules_per_target:
        class_examples = []
        for _, rule in enumerate(sorted(rules, key=lambda r: r.score,
                                        reverse=True)):
            examples = rule.examples()
            class_examples.append((rule._plain_conjunctions(),
                                   [ex.label for ex in examples]))
        examples_output.append((target_class, class_examples))
    return examples_output


def results_to_json(args, kb, rules_per_target, show_uris=False,
                    human=lambda label, rule: label):

    def rule_conditions_json(rule):
        conditions = []
        for pred in rule.predicates:

            label = pred.label
            if '#' in label and not show_uris:
                label = pred.label.split('#')[-1]
                label = human(label, rule)

            if isinstance(pred, UnaryPredicate):
                anno_names = rule.kb.annotation_name.get(pred.label, [DEFAULT_ANNOTATION_NAME])
                predicate_label = '_and_'.join(anno_names)
                
                if pred.negated:
                    predicate_label = '~' + predicate_label
                
                conj = {
                    "predicateName": predicate_label,
                    "predicateArguments": [
                        {
                            "argumentValue": pred.input_var,
                            "argumentType": "variable"
                        },
                        {
                            "argumentValue": label,
                            "argumentType": "constant"
                        }
                    ]
                }
            else:
                conj = {
                    "predicateName": label,
                    "predicateArguments": [
                        {
                            "argumentValue": pred.input_var,
                            "argumentType": "variable"
                        },
                        {
                            "argumentValue": pred.output_var,
                            "argumentType": "variable"
                        }
                    ]
                }
            conditions.append(conj)
        return conditions

    def rule_json(rule_id, rule):
        return {
            "ruleID": rule_id,
            "conditions": rule_conditions_json(rule),
            "predictions": [{
                "attribute": kb.class_name,
                "value": rule.target
            }],
            "weight": 1.0,
            "statistics": [{
                "statisticsType": "train",
                "numberOfExamples": rule.coverage,
                "measures": [
                    {
                        "measureName": "lift",
                        "value": rule.score
                    },
                    {
                        "measureName": "p-value",
                        "value": rule.pval
                    }
                ]
            }]
        }

    rule_set = []
    for target, rules in rules_per_target:
        for i, rule in enumerate(rules):
            rule_set.append(rule_json(i, rule))

    parameters_string = arguments_report(args, single_line=True)

    results = {
        "dataSpecification": {
            "attributes": [{
                "attributeName": "/",
                "attributeType": "numeric"
            }],
            "task": {
                "taskType": "Subgroup Discovery",
                "taskDescriptiveAttributes": ["/"],
                "taskClusteringAttributes": [],
                "taskTargetAttributes": [kb.class_name]
            },
            "query": "/"
        },
        "algorithmSpecification": {
            "name": "Hedwig",
            "parameters": parameters_string,
            "version": VERSION
        },
        "statistics": [{
            "statisticsType": "train",
            "numberOfExamples": len(kb.examples)
        }],
        "ruleSet": {
            "ruleSetID": str(uuid.uuid4()),
            "rules": rule_set,
            "interpretationMode": "DescriptiveUnordered"
        }
    }

    json_dump = json.dumps(results, indent=2)
    return json_dump
