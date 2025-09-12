#!/usr/bin/env python3
"""
Database Performance Analysis Tool
Command-line interface for comprehensive database analysis.
"""

import argparse
import sys
import os
import json
from src.analysis.comprehensive_analysis import (
    analyze_postgres_query_with_unused_indexes,
    analyze_mysql_query_with_unused_indexes,
    format_comprehensive_report
)

def validate_query(query):
    """Validate SQL query input."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Basic SQL validation
    query_upper = query.strip().upper()
    if not any(query_upper.startswith(keyword) for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']):
        raise ValueError("Query must start with a valid SQL keyword (SELECT, INSERT, UPDATE, DELETE, WITH)")
    
    return query.strip()

def validate_plan_file(plan_file):
    """Validate plan file exists and is readable."""
    if plan_file and not os.path.exists(plan_file):
        raise FileNotFoundError(f"Plan file not found: {plan_file}")
    return plan_file

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Database Performance Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze PostgreSQL query
  python analyze_db.py postgres "SELECT * FROM orders WHERE customer_id = 42;"
  
  # Analyze MySQL query
  python analyze_db.py mysql "SELECT * FROM orders WHERE customer_id = 42;"
  
  # Analyze with custom plan file
  python analyze_db.py postgres "SELECT * FROM orders WHERE customer_id = 42;" --plan-file artifacts/postgres/plans/pg_plan_1.json
  
  # Save results to file
  python analyze_db.py both "SELECT * FROM orders WHERE customer_id = 42;" --output results.json --format json
        """
    )
    
    parser.add_argument(
        'database',
        choices=['postgres', 'mysql', 'both'],
        help='Database type to analyze'
    )
    
    parser.add_argument(
        'query',
        help='SQL query to analyze'
    )
    
    parser.add_argument(
        '--plan-file',
        help='Path to existing query plan file (PostgreSQL only)'
    )
    
    parser.add_argument(
        '--output',
        help='Output file for results (default: stdout)'
    )
    
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    
    # Parse arguments with better error handling
    try:
        args = parser.parse_args()
    except SystemExit:
        # argparse already printed the error message
        sys.exit(1)
    
    # Validate inputs
    try:
        validated_query = validate_query(args.query)
        validated_plan_file = validate_plan_file(args.plan_file)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        results = {}
        
        if args.database in ['postgres', 'both']:
            print("Analyzing PostgreSQL query...")
            postgres_results = analyze_postgres_query_with_unused_indexes(
                validated_query, 
                validated_plan_file
            )
            results['postgresql'] = postgres_results
            
            if args.format == 'text':
                print("\n" + "="*80)
                print("POSTGRESQL ANALYSIS RESULTS")
                print("="*80)
                print(format_comprehensive_report(postgres_results))
            else:
                print(json.dumps(postgres_results, indent=2))
        
        if args.database in ['mysql', 'both']:
            print("\nAnalyzing MySQL query...")
            mysql_results = analyze_mysql_query_with_unused_indexes(validated_query)
            results['mysql'] = mysql_results
            
            if args.format == 'text':
                print("\n" + "="*80)
                print("MYSQL ANALYSIS RESULTS")
                print("="*80)
                print(format_comprehensive_report(mysql_results))
            else:
                print(json.dumps(mysql_results, indent=2))
        
        # Save results if output file specified
        if args.output:
            try:
                with open(args.output, 'w', encoding='utf-8') as f:
                    if args.format == 'json':
                        json.dump(results, f, indent=2)
                    else:
                        f.write(format_comprehensive_report(results.get('postgresql', results.get('mysql', {}))))
                print(f"\nResults saved to: {args.output}")
            except IOError as e:
                print(f"Error writing to output file: {e}", file=sys.stderr)
                sys.exit(1)
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Analysis error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
