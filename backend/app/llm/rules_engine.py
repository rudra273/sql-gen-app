from business_rules import run_all, export_rule_data
from business_rules.actions import BaseActions, rule_action
from business_rules.fields import FIELD_TEXT
from business_rules.variables import BaseVariables, string_rule_variable, boolean_rule_variable


class QueryVariables(BaseVariables):
    def __init__(self, query):
        self.query = query
        self.query_lower = query.lower()
    
    @string_rule_variable()
    def user_query(self):
        return self.query
    
    @boolean_rule_variable()
    def contains_date_filter(self):
        date_patterns = ['date', 'year', 'month', 'day', 'between', 'since', 'before', 'after']
        return any(pattern in self.query_lower for pattern in date_patterns)
    
    @boolean_rule_variable()
    def contains_group_by(self):
        group_patterns = ['group', 'average', 'sum', 'count', 'aggregate']
        return any(pattern in self.query_lower for pattern in group_patterns)
    
    @boolean_rule_variable()
    def contains_sorting(self):
        sort_patterns = ['sort', 'order', 'rank', 'top', 'bottom', 'highest', 'lowest']
        return any(pattern in self.query_lower for pattern in sort_patterns)
    

class QueryActions(BaseActions):
    def __init__(self, rules_list):
        self.rules_list = rules_list
    
    @rule_action(params={"rule": FIELD_TEXT})
    def add_rule(self, rule):
        if rule not in self.rules_list:
            self.rules_list.append(rule)


def get_query_specific_rules(user_query):
    """Generate query-specific rules based on the content of the user query"""
    rules_list = [
        "Use ONLY tables and columns from the schema",
        "Follow the exact schema for names",
        "Incorporate insights from additional context when available",
        "Ensure proper JOIN conditions",
        "Handle NULL values appropriately"
    ]
    
    variables = QueryVariables(user_query)
    actions = QueryActions(rules_list)
    
    rules = [
        # Date filtering rule
        {
            'conditions': {
                'all': [
                    {
                        'name': 'contains_date_filter',
                        'operator': 'is_true',
                        'value': True
                    }
                ]
            },
            'actions': [
                {
                    'name': 'add_rule',  
                    'params': {'rule': 'Use appropriate date functions for filtering (e.g., EXTRACT, DATE_TRUNC)'}
                }
            ]
        },
        # Group by rule
        {
            'conditions': {
                'all': [
                    {
                        'name': 'contains_group_by',
                        'operator': 'is_true',
                        'value': True
                    }
                ]
            },
            'actions': [
                {
                    'name': 'add_rule',
                    'params': {'rule': 'Use GROUP BY with appropriate aggregate functions (COUNT, SUM, AVG)'}
                }
            ]
        },
        # Sorting rule
        {
            'conditions': {
                'all': [
                    {
                        'name': 'contains_sorting',
                        'operator': 'is_true',
                        'value': True
                    }
                ]
            },
            'actions': [
                {
                    'name': 'add_rule',
                    'params': {'rule': 'Use ORDER BY with appropriate sorting direction (ASC/DESC)'}
                }
            ]
        }
    ]
    
    run_all(rule_list=rules,
            defined_variables=variables,
            defined_actions=actions)
    
    return rules_list
