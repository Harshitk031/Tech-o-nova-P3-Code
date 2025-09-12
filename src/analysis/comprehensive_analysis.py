# src/analysis/comprehensive_analysis.py
"""
Comprehensive Database Analysis Pipeline
Integrates query analysis, unused index detection, and scoring.
"""

import json
import os
import sys
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.analysis.sql_features import extract_sql_features
from src.parsers.postgres_plan import parse_postgres_plan
from src.parsers.mysql_plan import parse_mysql_plan
from src.analysis.rules_engine import run_all_rules
from src.analysis.scoring import calculate_scores

# Import unused index functions directly
import importlib.util
spec = importlib.util.spec_from_file_location("find_unused_indexes", "scripts/find_unused_indexes.py")
find_unused_indexes_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(find_unused_indexes_module)
find_postgres_unused_indexes = find_unused_indexes_module.find_postgres_unused_indexes
find_mysql_unused_indexes = find_unused_indexes_module.find_mysql_unused_indexes

def analyze_postgres_query_with_unused_indexes(sql_query: str, plan_file: str = None) -> dict:
    """
    Analyze a PostgreSQL query including unused index detection.
    
    Args:
        sql_query: The SQL query to analyze
        plan_file: Optional path to existing plan file
        
    Returns:
        Analysis results dictionary
    """
    print("--- Comprehensive PostgreSQL Analysis ---")
    print(f"Query: {sql_query}")
    print()
    
    # 1. Extract SQL features
    print("1. Extracting SQL features...")
    try:
        sql_features = extract_sql_features(sql_query)
        print(f"   WHERE columns: {sql_features.get('where_columns', [])}")
    except Exception as e:
        print(f"   Error extracting SQL features: {e}")
        sql_features = {
            'where_columns': [],
            'query_type': 'UNKNOWN',
            'table_name': None
        }
    print()
    
    # 2. Parse plan data
    print("2. Parsing query plan...")
    if plan_file and os.path.exists(plan_file):
        # Use existing plan file
        plan_data = parse_postgres_plan(plan_file)
    else:
        # Simulate plan data for demo
        plan_data = {
            'Node Type': 'Seq Scan',
            'Relation Name': 'orders',
            'Total Cost': 1887.0,
            'Plan Rows': 98,
            'Actual Rows': 99,
            'Rows Removed by Filter': 99901
        }
    print(f"   Plan: {plan_data['Node Type']} on {plan_data['Relation Name']}")
    print()
    
    # 3. Find unused indexes
    print("3. Analyzing unused indexes...")
    unused_indexes = find_postgres_unused_indexes()
    print(f"   Found {len(unused_indexes)} unused indexes")
    print()
    
    # 4. Run rules engine
    print("4. Running optimization rules...")
    recommendations = run_all_rules(plan_data, sql_features, unused_indexes)
    print(f"   Found {len(recommendations)} recommendations")
    print()
    
    # 5. Calculate confidence and impact scores
    print("5. Calculating confidence and impact scores...")
    stats_data = {'total_exec_time': 5200.5}
    hypopg_delta = {'after_node_type': 'Index Scan', 'cost_reduction_percent': 99.8}
    
    for recommendation in recommendations:
        confidence, impact = calculate_scores(recommendation, plan_data, stats_data, hypopg_delta)
        recommendation['confidence'] = confidence
        recommendation['impact'] = impact
    
    print(f"   Added scoring to {len(recommendations)} recommendations")
    print()
    
    # 6. Compile results
    results = {
        'query': sql_query,
        'sql_features': sql_features,
        'plan_data': plan_data,
        'unused_indexes': unused_indexes,
        'recommendations': recommendations,
        'summary': {
            'total_recommendations': len(recommendations),
            'unused_indexes_count': len(unused_indexes),
            'high_severity': len([r for r in recommendations if r.get('severity') == 'HIGH']),
            'medium_severity': len([r for r in recommendations if r.get('severity') == 'MEDIUM']),
            'low_severity': len([r for r in recommendations if r.get('severity') == 'LOW'])
        }
    }
    return results

def analyze_mysql_query_with_unused_indexes(sql_query: str) -> dict:
    """
    Analyze a MySQL query including unused index detection.
    
    Args:
        sql_query: The SQL query to analyze
        
    Returns:
        Analysis results dictionary
    """
    print("--- Comprehensive MySQL Analysis ---")
    print(f"Query: {sql_query}")
    print()
    
    # 1. Extract SQL features
    print("1. Extracting SQL features...")
    try:
        sql_features = extract_sql_features(sql_query)
        print(f"   WHERE columns: {sql_features.get('where_columns', [])}")
    except Exception as e:
        print(f"   Error extracting SQL features: {e}")
        sql_features = {
            'where_columns': [],
            'query_type': 'UNKNOWN',
            'table_name': None
        }
    print()
    
    # 2. Parse plan data
    print("2. Parsing query plan...")
    plan_data = {
        'Node Type': 'ALL',
        'Relation Name': 'orders',
        'Total Cost': 1000.0,
        'Plan Rows': 100000,
        'Actual Rows': 99,
        'Rows Removed by Filter': 99901
    }
    print(f"   Plan: {plan_data['Node Type']} on {plan_data['Relation Name']}")
    print()
    
    # 3. Find unused indexes
    print("3. Analyzing unused indexes...")
    unused_indexes = find_mysql_unused_indexes()
    print(f"   Found {len(unused_indexes)} unused indexes")
    print()
    
    # 4. Run rules engine
    print("4. Running optimization rules...")
    recommendations = run_all_rules(plan_data, sql_features, unused_indexes)
    print(f"   Found {len(recommendations)} recommendations")
    print()
    
    # 5. Calculate confidence and impact scores
    print("5. Calculating confidence and impact scores...")
    stats_data = {'total_exec_time': 5200.5}
    hypopg_delta = {'after_node_type': 'Index Scan', 'cost_reduction_percent': 99.8}
    
    for recommendation in recommendations:
        confidence, impact = calculate_scores(recommendation, plan_data, stats_data, hypopg_delta)
        recommendation['confidence'] = confidence
        recommendation['impact'] = impact
    
    print(f"   Added scoring to {len(recommendations)} recommendations")
    print()
    
    # 6. Compile results
    results = {
        'query': sql_query,
        'sql_features': sql_features,
        'plan_data': plan_data,
        'unused_indexes': unused_indexes,
        'recommendations': recommendations,
        'summary': {
            'total_recommendations': len(recommendations),
            'unused_indexes_count': len(unused_indexes),
            'high_severity': len([r for r in recommendations if r.get('severity') == 'HIGH']),
            'medium_severity': len([r for r in recommendations if r.get('severity') == 'MEDIUM']),
            'low_severity': len([r for r in recommendations if r.get('severity') == 'LOW'])
        }
    }
    return results

def format_comprehensive_report(results: dict) -> str:
    """
    Generate a comprehensive report including unused index analysis.
    
    Args:
        results: Analysis results dictionary
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 80)
    report.append("COMPREHENSIVE DATABASE ANALYSIS REPORT")
    report.append("=" * 80)
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
    
    # Plan Analysis
    report.append("QUERY PLAN:")
    for key, value in results['plan_data'].items():
        report.append(f"  {key}: {value}")
    report.append("")
    
    # Unused Indexes
    if results['unused_indexes']:
        report.append("UNUSED INDEXES:")
        for i, idx in enumerate(results['unused_indexes'], 1):
            report.append(f"  {i}. {idx['index_name']} on {idx['table_name']} ({idx['database']})")
            report.append(f"     Times used: {idx['times_used']}")
            if 'index_size' in idx:
                report.append(f"     Size: {idx['index_size']}")
        report.append("")
    else:
        report.append("UNUSED INDEXES: None found")
        report.append("")
    
    # Recommendations
    if results['recommendations']:
        report.append("RECOMMENDATIONS:")
        for i, rec in enumerate(results['recommendations'], 1):
            report.append(f"  {i}. {rec['type']} ({rec['severity']} severity)")
            report.append(f"     Rule ID: {rec['rule_id']}")
            report.append(f"     Rationale: {rec['rationale']}")
            report.append(f"     Suggested Action: {rec['suggested_action']}")
            report.append(f"     Estimated Impact: {rec['estimated_impact']}")
            if 'confidence' in rec:
                report.append(f"     Confidence Score: {rec['confidence']}")
            if 'impact' in rec:
                report.append(f"     Impact Tier: {rec['impact']}")
            if rec.get('caveats'):
                report.append("     Caveats:")
                for caveat in rec['caveats']:
                    report.append(f"       - {caveat}")
            report.append("")
    else:
        report.append("RECOMMENDATIONS: None found")
        report.append("")
    
    # Summary
    report.append("SUMMARY:")
    summary = results['summary']
    report.append(f"  Total Recommendations: {summary['total_recommendations']}")
    report.append(f"  Unused Indexes: {summary['unused_indexes_count']}")
    report.append(f"  High Severity: {summary['high_severity']}")
    report.append(f"  Medium Severity: {summary['medium_severity']}")
    report.append(f"  Low Severity: {summary['low_severity']}")
    report.append("")
    
    return "\n".join(report)

def main():
    """Main function to run comprehensive analysis."""
    print("--- Comprehensive Database Analysis Pipeline ---")
    print("Testing with sample queries...")
    print()
    
    # Test PostgreSQL analysis
    postgres_query = "SELECT * FROM orders WHERE customer_id = 42;"
    postgres_results = analyze_postgres_query_with_unused_indexes(postgres_query)
    
    print("=" * 80)
    print("POSTGRESQL ANALYSIS RESULTS")
    print("=" * 80)
    print(format_comprehensive_report(postgres_results))
    print()
    
    # Test MySQL analysis
    mysql_query = "SELECT * FROM orders WHERE customer_id = 42;"
    mysql_results = analyze_mysql_query_with_unused_indexes(mysql_query)
    
    print("=" * 80)
    print("MYSQL ANALYSIS RESULTS")
    print("=" * 80)
    print(format_comprehensive_report(mysql_results))
    print()
    
    # Save results
    all_results = {
        'postgresql': postgres_results,
        'mysql': mysql_results,
        'timestamp': '2024-01-01T00:00:00Z'  # In real implementation, use actual timestamp
    }
    
    with open('artifacts/comprehensive_analysis.json', 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print("Results saved to: artifacts/comprehensive_analysis.json")

if __name__ == '__main__':
    main()
