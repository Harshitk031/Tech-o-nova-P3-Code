# src/analysis/integrated_pipeline.py
"""
Integrated Database Analysis Pipeline
Combines plan parsing, SQL feature extraction, rules engine, and scoring.
"""

import json
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.parsers.postgres_plan import parse_postgres_plan
from src.parsers.mysql_plan import parse_mysql_plan
from src.analysis.sql_features import extract_sql_features
from src.analysis.rules_engine import run_all_rules, format_recommendations
from src.analysis.scoring import calculate_scores

def analyze_postgres_query(sql_query: str, plan_file: str = None) -> dict:
    """
    Complete analysis pipeline for PostgreSQL queries.
    
    Args:
        sql_query: The SQL query to analyze
        plan_file: Optional path to existing plan file
        
    Returns:
        Dictionary containing analysis results
    """
    print("--- PostgreSQL Query Analysis Pipeline ---")
    print(f"Query: {sql_query}")
    print()
    
    # 1. Extract SQL features
    print("1. Extracting SQL features...")
    where_columns = extract_sql_features(sql_query)
    sql_features = {
        'where_columns': where_columns,
        'query_type': 'SELECT',
        'table_name': 'orders'
    }
    print(f"   WHERE columns: {where_columns}")
    print()
    
    # 2. Parse query plan (simulate for now)
    print("2. Parsing query plan...")
    if plan_file and os.path.exists(plan_file):
        # In a real implementation, you'd parse the actual plan file
        plan_data = {
            'Node Type': 'Seq Scan',
            'Relation Name': 'orders',
            'Total Cost': 1887.0,
            'Plan Rows': 98,
            'Actual Rows': 99,
            'Rows Removed by Filter': 99901  # Added for scoring
        }
    else:
        # Simulated plan data
        plan_data = {
            'Node Type': 'Seq Scan',
            'Relation Name': 'orders',
            'Total Cost': 1887.0,
            'Plan Rows': 98,
            'Actual Rows': 99,
            'Rows Removed by Filter': 99901  # Added for scoring
        }
    print(f"   Plan: {plan_data['Node Type']} on {plan_data['Relation Name']}")
    print()
    
    # 3. Run rules engine
    print("3. Running optimization rules...")
    recommendations = run_all_rules(plan_data, sql_features)
    print(f"   Found {len(recommendations)} recommendations")
    print()
    
    # 4. Add confidence and impact scoring
    print("4. Calculating confidence and impact scores...")
    stats_data = {'total_exec_time': 5200.5}  # Simulated stats data
    hypopg_delta = {'after_node_type': 'Index Scan', 'cost_reduction_percent': 99.8}  # Simulated HypoPG data
    
    for recommendation in recommendations:
        confidence, impact = calculate_scores(recommendation, plan_data, stats_data, hypopg_delta)
        recommendation['confidence'] = confidence
        recommendation['impact'] = impact
    
    print(f"   Added scoring to {len(recommendations)} recommendations")
    print()
    
    # 5. Compile results
    results = {
        'query': sql_query,
        'sql_features': sql_features,
        'plan_data': plan_data,
        'recommendations': recommendations,
        'summary': {
            'total_recommendations': len(recommendations),
            'high_severity': len([r for r in recommendations if r.get('severity') == 'HIGH']),
            'medium_severity': len([r for r in recommendations if r.get('severity') == 'MEDIUM']),
            'low_severity': len([r for r in recommendations if r.get('severity') == 'LOW'])
        }
    }
    
    return results

def analyze_mysql_query(sql_query: str) -> dict:
    """
    Complete analysis pipeline for MySQL queries.
    
    Args:
        sql_query: The SQL query to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    print("--- MySQL Query Analysis Pipeline ---")
    print(f"Query: {sql_query}")
    print()
    
    # 1. Extract SQL features
    print("1. Extracting SQL features...")
    where_columns = extract_sql_features(sql_query)
    sql_features = {
        'where_columns': where_columns,
        'query_type': 'SELECT',
        'table_name': 'orders'
    }
    print(f"   WHERE columns: {where_columns}")
    print()
    
    # 2. Parse query plan (simulate for now)
    print("2. Parsing query plan...")
    plan_data = {
        'Node Type': 'ALL',
        'Relation Name': 'orders',
        'Total Cost': 1000.0,  # MySQL doesn't use same cost model
        'Plan Rows': 100000,
        'Actual Rows': 99,
        'Rows Removed by Filter': 99901  # Added for scoring
    }
    print(f"   Plan: {plan_data['Node Type']} on {plan_data['Relation Name']}")
    print()
    
    # 3. Run rules engine
    print("3. Running optimization rules...")
    recommendations = run_all_rules(plan_data, sql_features)
    print(f"   Found {len(recommendations)} recommendations")
    print()
    
    # 4. Add confidence and impact scoring
    print("4. Calculating confidence and impact scores...")
    stats_data = {'total_exec_time': 5200.5}  # Simulated stats data
    hypopg_delta = {'after_node_type': 'Index Scan', 'cost_reduction_percent': 99.8}  # Simulated HypoPG data
    
    for recommendation in recommendations:
        confidence, impact = calculate_scores(recommendation, plan_data, stats_data, hypopg_delta)
        recommendation['confidence'] = confidence
        recommendation['impact'] = impact
    
    print(f"   Added scoring to {len(recommendations)} recommendations")
    print()
    
    # 5. Compile results
    results = {
        'query': sql_query,
        'sql_features': sql_features,
        'plan_data': plan_data,
        'recommendations': recommendations,
        'summary': {
            'total_recommendations': len(recommendations),
            'high_severity': len([r for r in recommendations if r.get('severity') == 'HIGH']),
            'medium_severity': len([r for r in recommendations if r.get('severity') == 'MEDIUM']),
            'low_severity': len([r for r in recommendations if r.get('severity') == 'LOW'])
        }
    }
    
    return results

def format_recommendations_with_scoring(recommendations: list) -> str:
    """
    Format recommendations with confidence and impact scores.
    
    Args:
        recommendations: List of recommendation dictionaries
        
    Returns:
        Formatted string
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
        output.append(f"Confidence Score: {rec.get('confidence', 'N/A')}")
        output.append(f"Impact Tier: {rec.get('impact', 'N/A')}")
        
        if rec.get('caveats'):
            output.append("Caveats:")
            for caveat in rec['caveats']:
                output.append(f"  - {caveat}")
        output.append("")
    
    return "\n".join(output)

def generate_report(results: dict) -> str:
    """
    Generate a comprehensive analysis report.
    
    Args:
        results: Analysis results dictionary
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 60)
    report.append("DATABASE QUERY ANALYSIS REPORT")
    report.append("=" * 60)
    report.append("")
    
    # Query information
    report.append("QUERY:")
    report.append(f"  {results['query']}")
    report.append("")
    
    # SQL Features
    report.append("SQL FEATURES:")
    for key, value in results['sql_features'].items():
        report.append(f"  {key}: {value}")
    report.append("")
    
    # Plan Information
    report.append("EXECUTION PLAN:")
    for key, value in results['plan_data'].items():
        report.append(f"  {key}: {value}")
    report.append("")
    
    # Summary
    summary = results['summary']
    report.append("ANALYSIS SUMMARY:")
    report.append(f"  Total Recommendations: {summary['total_recommendations']}")
    report.append(f"  High Severity: {summary['high_severity']}")
    report.append(f"  Medium Severity: {summary['medium_severity']}")
    report.append(f"  Low Severity: {summary['low_severity']}")
    report.append("")
    
    # Recommendations with scoring
    if results['recommendations']:
        report.append("RECOMMENDATIONS:")
        report.append(format_recommendations_with_scoring(results['recommendations']))
    else:
        report.append("RECOMMENDATIONS: None found")
    
    return "\n".join(report)

def main():
    """Main function to demonstrate the integrated pipeline."""
    
    # Test queries
    test_queries = [
        "SELECT * FROM orders WHERE customer_id = 42;",
        "SELECT * FROM orders WHERE amount > 450 ORDER BY created_at DESC;",
        "SELECT * FROM orders WHERE customer_id = 101 AND amount > 200;"
    ]
    
    print("--- Integrated Database Analysis Pipeline with Scoring ---")
    print("Testing with sample queries...")
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"TEST CASE #{i}")
        print("-" * 40)
        
        # Analyze the query
        results = analyze_postgres_query(query)
        
        # Generate and display report
        report = generate_report(results)
        print(report)
        print()
        print("=" * 60)
        print()

if __name__ == '__main__':
    main()
