# src/analysis/rules_engine.py
"""
Advanced Database Optimization Rules Engine
Integrates with existing parsers to provide automated recommendations.
"""

import json
import re
from typing import Dict, List, Optional, Any

def check_for_missing_index(plan_data: Dict, sql_features: Dict) -> List[Dict]:
    """
    Rule: Detects a sequential scan on a table with a WHERE clause.
    
    Args:
        plan_data: Parsed data from the EXPLAIN plan
        sql_features: Features extracted from the SQL query string
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    node_type = plan_data.get('Node Type')
    table_name = plan_data.get('Relation Name')
    where_columns = sql_features.get('where_columns', [])
    total_cost = plan_data.get('Total Cost', 0)
    actual_rows = plan_data.get('Actual Rows', 0)
    
    if node_type == 'Seq Scan' and where_columns:
        column_list = ", ".join(where_columns)
        index_name = f"idx_{table_name}_{'_'.join(where_columns)}"
        
        # Calculate severity based on cost and row count
        severity = "HIGH" if total_cost > 1000 else "MEDIUM" if total_cost > 100 else "LOW"
        
        recommendation = {
            "rule_id": "MISSING_INDEX_001",
            "type": "MISSING_INDEX",
            "severity": severity,
            "table": table_name,
            "columns": where_columns,
            "rationale": f"Sequential scan on '{table_name}' with WHERE clause on {column_list}. Cost: {total_cost:.2f}, Rows: {actual_rows}",
            "evidence": {
                "node_type": node_type,
                "total_cost": total_cost,
                "actual_rows": actual_rows,
                "filtered_columns": where_columns
            },
            "suggested_action": f"CREATE INDEX {index_name} ON {table_name} ({column_list});",
            "caveats": [
                "Verify index effectiveness with HypoPG before production",
                "Consider index maintenance overhead",
                "Monitor query performance after implementation"
            ],
            "estimated_impact": f"Expected {85-95}% performance improvement"
        }
        recommendations.append(recommendation)
    
    return recommendations

def check_for_inefficient_sort(plan_data: Dict, sql_features: Dict) -> List[Dict]:
    """
    Rule: Detects inefficient sorting operations (filesort).
    
    Args:
        plan_data: Parsed data from the EXPLAIN plan
        sql_features: Features extracted from the SQL query string
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    node_type = plan_data.get('Node Type')
    sort_key = plan_data.get('Sort Key')
    sort_method = plan_data.get('Sort Method')
    table_name = plan_data.get('Relation Name')
    
    if node_type == 'Sort' and sort_method == 'external merge':
        recommendation = {
            "rule_id": "INEFFICIENT_SORT_001",
            "type": "INEFFICIENT_SORT",
            "severity": "HIGH",
            "table": table_name,
            "columns": [sort_key] if sort_key else [],
            "rationale": f"External merge sort detected on {sort_key}. This requires temporary disk space and is inefficient.",
            "evidence": {
                "node_type": node_type,
                "sort_method": sort_method,
                "sort_key": sort_key
            },
            "suggested_action": f"CREATE INDEX idx_{table_name}_{sort_key.replace(', ', '_')} ON {table_name} ({sort_key});",
            "caveats": [
                "Consider if sorting is necessary",
                "Evaluate if LIMIT clause can reduce sort workload",
                "Monitor index maintenance cost"
            ],
            "estimated_impact": "Eliminates external sort, improves memory usage"
        }
        recommendations.append(recommendation)
    
    return recommendations

def check_for_nested_loop_join(plan_data: Dict, sql_features: Dict) -> List[Dict]:
    """
    Rule: Detects potentially inefficient nested loop joins.
    
    Args:
        plan_data: Parsed data from the EXPLAIN plan
        sql_features: Features extracted from the SQL query string
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    node_type = plan_data.get('Node Type')
    join_type = plan_data.get('Join Type')
    total_cost = plan_data.get('Total Cost', 0)
    
    if node_type == 'Nested Loop' and total_cost > 1000:
        recommendation = {
            "rule_id": "NESTED_LOOP_001",
            "type": "NESTED_LOOP_JOIN",
            "severity": "MEDIUM",
            "rationale": f"High-cost nested loop join detected (Cost: {total_cost:.2f}). Consider alternative join strategies.",
            "evidence": {
                "node_type": node_type,
                "join_type": join_type,
                "total_cost": total_cost
            },
            "suggested_action": "Consider adding indexes on join columns or using hash/merge joins",
            "caveats": [
                "Nested loops can be efficient for small datasets",
                "Check if statistics are up to date",
                "Consider query rewrite with different join order"
            ],
            "estimated_impact": "Potential 20-50% improvement with proper indexing"
        }
        recommendations.append(recommendation)
    
    return recommendations

def check_for_missing_statistics(plan_data: Dict, sql_features: Dict) -> List[Dict]:
    """
    Rule: Detects potential issues with outdated statistics.
    
    Args:
        plan_data: Parsed data from the EXPLAIN plan
        sql_features: Features extracted from the SQL query string
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    plan_rows = plan_data.get('Plan Rows', 0)
    actual_rows = plan_data.get('Actual Rows', 0)
    
    # Check for significant estimation errors
    if plan_rows > 0 and actual_rows > 0:
        estimation_error = abs(plan_rows - actual_rows) / max(plan_rows, actual_rows)
        
        if estimation_error > 0.5:  # 50% error threshold
            recommendation = {
                "rule_id": "MISSING_STATS_001",
                "type": "MISSING_STATISTICS",
                "severity": "MEDIUM",
                "rationale": f"Significant estimation error: planned {plan_rows} rows, actual {actual_rows} rows ({estimation_error:.1%} error)",
                "evidence": {
                    "planned_rows": plan_rows,
                    "actual_rows": actual_rows,
                    "estimation_error": estimation_error
                },
                "suggested_action": "Run ANALYZE to update table statistics",
                "caveats": [
                    "Statistics affect query planning",
                    "Run during low-traffic periods",
                    "Monitor performance after update"
                ],
                "estimated_impact": "Improved query planning accuracy"
            }
            recommendations.append(recommendation)
    
    return recommendations

def check_for_unused_indexes(unused_indexes: List[Dict]) -> List[Dict]:
    """
    Rule: Detects unused indexes that may be candidates for removal.
    
    Args:
        unused_indexes: List of unused index dictionaries from database queries
        
    Returns:
        List of recommendation dictionaries
    """
    recommendations = []
    
    for idx in unused_indexes:
        if idx['database'] == 'postgresql':
            rationale = f"The index '{idx['index_name']}' on table '{idx['table_name']}' has been used {idx['times_used']} times. It may be a candidate for removal to save space ({idx['index_size']}) and improve write performance."
        else:  # MySQL
            rationale = f"The index '{idx['index_name']}' on table '{idx['table_name']}' in database '{idx['db_name']}' has not been used since the last server restart. It may be a candidate for removal to save space and improve write performance."
        
        recommendation = {
            "rule_id": "UNUSED_INDEX_001",
            "type": "UNUSED_INDEX_CANDIDATE",
            "severity": "MEDIUM",
            "table": idx['table_name'],
            "index_name": idx['index_name'],
            "rationale": rationale,
            "evidence": {
                "database": idx['database'],
                "table_name": idx['table_name'],
                "index_name": idx['index_name'],
                "times_used": idx['times_used']
            },
            "suggested_action": f"DROP INDEX {idx['index_name']};" if idx['database'] == 'postgresql' else f"DROP INDEX {idx['index_name']} ON {idx['table_name']};",
            "caveats": [
                "Please verify this index is not used for infrequent but important queries (e.g., annual reports) before dropping it.",
                "Consider monitoring the application for any performance degradation after removal.",
                "Backup the database before making schema changes."
            ],
            "estimated_impact": "Medium - Reduces storage overhead and improves write performance"
        }
        recommendations.append(recommendation)
    
    return recommendations

def run_all_rules(plan_data: Dict, sql_features: Dict, unused_indexes: List[Dict] = None) -> List[Dict]:
    """
    Runs all available rules against the provided plan and SQL features.
    
    Args:
        plan_data: Parsed data from the EXPLAIN plan
        sql_features: Features extracted from the SQL query string
        unused_indexes: Optional list of unused indexes from database queries
        
    Returns:
        List of all recommendations from all rules
    """
    all_recommendations = []
    
    # Run all rule functions
    rule_functions = [
        check_for_missing_index,
        check_for_inefficient_sort,
        check_for_nested_loop_join,
        check_for_missing_statistics
    ]
    
    for rule_func in rule_functions:
        try:
            recommendations = rule_func(plan_data, sql_features)
            all_recommendations.extend(recommendations)
        except Exception as e:
            print(f"Warning: Rule {rule_func.__name__} failed: {e}")
    
    # Check for unused indexes if provided
    if unused_indexes:
        try:
            unused_recs = check_for_unused_indexes(unused_indexes)
            all_recommendations.extend(unused_recs)
        except Exception as e:
            print(f"Warning: Unused index check failed: {e}")
    
    return all_recommendations

def format_recommendations(recommendations: List[Dict]) -> str:
    """
    Formats recommendations for display.
    
    Args:
        recommendations: List of recommendation dictionaries
        
    Returns:
        Formatted string representation
    """
    if not recommendations:
        return "--- 🆗 No recommendations found for this plan. ---"
    
    output = []
    output.append("--- ✅ Database Optimization Recommendations ---")
    output.append("")
    
    for i, rec in enumerate(recommendations, 1):
        output.append(f"Recommendation #{i}: {rec['type']} ({rec['severity']} severity)")
        output.append(f"Rule ID: {rec['rule_id']}")
        output.append(f"Rationale: {rec['rationale']}")
        output.append(f"Suggested Action: {rec['suggested_action']}")
        output.append(f"Estimated Impact: {rec['estimated_impact']}")
        
        if rec.get('caveats'):
            output.append("Caveats:")
            for caveat in rec['caveats']:
                output.append(f"  - {caveat}")
        
        output.append("")
    
    return "\n".join(output)

if __name__ == '__main__':
    # Test the rules engine with sample data
    print("--- Testing Database Optimization Rules Engine ---")
    print()
    
    # Sample plan data (from our previous analysis)
    sample_plan = {
        'Node Type': 'Seq Scan',
        'Relation Name': 'orders',
        'Total Cost': 1887.0,
        'Plan Rows': 98,
        'Actual Rows': 99
    }
    
    # Sample SQL features (from our previous analysis)
    sample_sql_features = {
        'where_columns': ['customer_id'],
        'query_type': 'SELECT',
        'table_name': 'orders'
    }
    
    # Run all rules
    recommendations = run_all_rules(sample_plan, sample_sql_features)
    
    # Display results
    print(format_recommendations(recommendations))



