#!/usr/bin/env python3
"""
Database Performance Analysis Tool - Demo Script
Demonstrates all capabilities of the analysis tool.
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_section(title):
    """Print a formatted section header."""
    print(f"\n--- {title} ---")

def main():
    """Run the complete demo."""
    print_header("DATABASE PERFORMANCE ANALYSIS TOOL - DEMO")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test queries
    test_queries = [
        "SELECT * FROM orders WHERE customer_id = 42;",
        "SELECT * FROM orders WHERE amount > 450 ORDER BY created_at DESC;",
        "SELECT o.*, l.product_id FROM orders o JOIN line_items l ON o.id = l.order_id WHERE o.customer_id = 100;"
    ]
    
    print_section("1. Testing Individual Components")
    
    # Test SQL feature extraction
    print("\n1.1 SQL Feature Extraction")
    from src.analysis.sql_features import extract_sql_features
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        features = extract_sql_features(query)
        print(f"Features: {features}")
    
    # Test scoring system
    print_section("1.2 Scoring System")
    from src.analysis.scoring import calculate_scores
    
    sample_recommendation = {
        "type": "MISSING_INDEX",
        "suggested_action": "CREATE INDEX ON orders (customer_id);"
    }
    sample_plan = {'Node Type': 'Seq Scan', 'Rows Removed by Filter': 99901, 'Actual Rows': 99}
    sample_stats = {'total_exec_time': 5200.5}
    sample_hypopg = {'after_node_type': 'Index Scan', 'cost_reduction_percent': 99.8}
    
    confidence, impact = calculate_scores(sample_recommendation, sample_plan, sample_stats, sample_hypopg)
    print(f"Sample Recommendation Scoring:")
    print(f"  Confidence: {confidence}")
    print(f"  Impact: {impact}")
    
    # Test rules engine
    print_section("1.3 Rules Engine")
    from src.analysis.rules_engine import run_all_rules
    
    sample_plan_data = {
        'Node Type': 'Seq Scan',
        'Relation Name': 'orders',
        'Total Cost': 1887.0,
        'Plan Rows': 98,
        'Actual Rows': 99
    }
    sample_sql_features = {
        'where_columns': ['customer_id'],
        'query_type': 'SELECT',
        'table_name': 'orders'
    }
    
    recommendations = run_all_rules(sample_plan_data, sample_sql_features)
    print(f"Generated {len(recommendations)} recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec['type']} ({rec['severity']}) - {rec['rationale']}")
    
    print_section("2. Testing Unused Index Detection")
    
    # Test unused index detection
    import importlib.util
    spec = importlib.util.spec_from_file_location("find_unused_indexes", "scripts/find_unused_indexes.py")
    find_unused_indexes_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(find_unused_indexes_module)
    find_postgres_unused_indexes = find_unused_indexes_module.find_postgres_unused_indexes
    find_mysql_unused_indexes = find_unused_indexes_module.find_mysql_unused_indexes
    
    print("\n2.1 PostgreSQL Unused Indexes")
    postgres_unused = find_postgres_unused_indexes()
    print(f"Found {len(postgres_unused)} unused indexes in PostgreSQL")
    for idx in postgres_unused:
        print(f"  - {idx['index_name']} on {idx['table_name']} (used {idx['times_used']} times, {idx['index_size']})")
    
    print("\n2.2 MySQL Unused Indexes")
    mysql_unused = find_mysql_unused_indexes()
    print(f"Found {len(mysql_unused)} unused indexes in MySQL")
    for idx in mysql_unused:
        print(f"  - {idx['index_name']} on {idx['table_name']} (used {idx['times_used']} times)")
    
    print_section("3. Testing Comprehensive Analysis")
    
    # Test comprehensive analysis
    from src.analysis.comprehensive_analysis import (
        analyze_postgres_query_with_unused_indexes,
        analyze_mysql_query_with_unused_indexes
    )
    
    print("\n3.1 PostgreSQL Comprehensive Analysis")
    postgres_query = "SELECT * FROM orders WHERE customer_id = 42;"
    postgres_results = analyze_postgres_query_with_unused_indexes(postgres_query)
    
    print(f"\nPostgreSQL Analysis Summary:")
    print(f"  Query: {postgres_results['query']}")
    print(f"  Recommendations: {postgres_results['summary']['total_recommendations']}")
    print(f"  Unused Indexes: {postgres_results['summary']['unused_indexes_count']}")
    print(f"  High Severity: {postgres_results['summary']['high_severity']}")
    print(f"  Medium Severity: {postgres_results['summary']['medium_severity']}")
    print(f"  Low Severity: {postgres_results['summary']['low_severity']}")
    
    print("\n3.2 MySQL Comprehensive Analysis")
    mysql_query = "SELECT * FROM orders WHERE customer_id = 42;"
    mysql_results = analyze_mysql_query_with_unused_indexes(mysql_query)
    
    print(f"\nMySQL Analysis Summary:")
    print(f"  Query: {mysql_results['query']}")
    print(f"  Recommendations: {mysql_results['summary']['total_recommendations']}")
    print(f"  Unused Indexes: {mysql_results['summary']['unused_indexes_count']}")
    print(f"  High Severity: {mysql_results['summary']['high_severity']}")
    print(f"  Medium Severity: {mysql_results['summary']['medium_severity']}")
    print(f"  Low Severity: {mysql_results['summary']['low_severity']}")
    
    print_section("4. Testing CLI Interface")
    
    print("\n4.1 CLI Help")
    print("Run 'python analyze_db.py --help' to see all available options")
    
    print("\n4.2 Sample CLI Commands")
    print("  # Analyze PostgreSQL query:")
    print("  python analyze_db.py postgres \"SELECT * FROM orders WHERE customer_id = 42;\"")
    print()
    print("  # Analyze MySQL query:")
    print("  python analyze_db.py mysql \"SELECT * FROM orders WHERE customer_id = 42;\"")
    print()
    print("  # Analyze both databases:")
    print("  python analyze_db.py both \"SELECT * FROM orders WHERE customer_id = 42;\"")
    print()
    print("  # Save results to file:")
    print("  python analyze_db.py postgres \"SELECT * FROM orders WHERE customer_id = 42;\" --output results.txt")
    print()
    print("  # JSON output format:")
    print("  python analyze_db.py postgres \"SELECT * FROM orders WHERE customer_id = 42;\" --format json")
    
    print_section("5. Generated Artifacts")
    
    # List generated artifacts
    artifacts_dir = "artifacts"
    if os.path.exists(artifacts_dir):
        print(f"\nGenerated artifacts in '{artifacts_dir}':")
        for root, dirs, files in os.walk(artifacts_dir):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file_path} ({file_size} bytes)")
    else:
        print(f"\nNo artifacts directory found. Run analysis to generate artifacts.")
    
    print_section("6. System Capabilities Summary")
    
    capabilities = [
        "✅ SQL Query Parsing and Feature Extraction",
        "✅ PostgreSQL Query Plan Analysis",
        "✅ MySQL Query Plan Analysis", 
        "✅ Unused Index Detection (PostgreSQL & MySQL)",
        "✅ Automated Optimization Recommendations",
        "✅ Confidence and Impact Scoring",
        "✅ Multiple Rule Types (Missing Index, Unused Index, Inefficient Sort, Statistics)",
        "✅ Command Line Interface",
        "✅ JSON and Text Output Formats",
        "✅ Comprehensive Reporting",
        "✅ Docker-based Database Setup",
        "✅ Cross-Database Analysis Support"
    ]
    
    print("\nSystem Capabilities:")
    for capability in capabilities:
        print(f"  {capability}")
    
    print_section("7. Next Steps")
    
    next_steps = [
        "1. Run 'python analyze_db.py --help' to see all CLI options",
        "2. Test with your own SQL queries using the CLI interface",
        "3. Review generated artifacts in the 'artifacts/' directory",
        "4. Customize rules in 'src/analysis/rules_engine.py' for your specific needs",
        "5. Extend the scoring system in 'src/analysis/scoring.py' for better accuracy",
        "6. Add new database types by extending the parsers in 'src/parsers/'",
        "7. Integrate with your CI/CD pipeline for automated database optimization"
    ]
    
    print("\nRecommended Next Steps:")
    for step in next_steps:
        print(f"  {step}")
    
    print_header("DEMO COMPLETE")
    print("The Database Performance Analysis Tool is ready for use!")
    print("For more information, see the README.md file.")

if __name__ == '__main__':
    main()
