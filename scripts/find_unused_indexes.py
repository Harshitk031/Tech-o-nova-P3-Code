# scripts/find_unused_indexes.py
"""
Find Unused Indexes Script
Identifies indexes that have never or rarely been used for scans.
"""

import psycopg2
import mysql.connector
import json
import sys
import os
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database_config import get_database_config

# Get database configuration
db_config = get_database_config()
POSTGRES_CONN_STR = db_config.get_postgres_connection_string()
MYSQL_CONFIG = db_config.get_mysql_config()

def find_postgres_unused_indexes() -> List[Dict[str, Any]]:
    """
    Find unused indexes in PostgreSQL using pg_stat_user_indexes.
    
    Returns:
        List of unused index dictionaries
    """
    try:
        conn = psycopg2.connect(POSTGRES_CONN_STR)
        conn.autocommit = True
        
        with conn.cursor() as cur:
            # Query for unused indexes
            cur.execute("""
                SELECT
                    relname AS table_name,
                    indexrelname AS index_name,
                    idx_scan AS times_used,
                    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
                FROM
                    pg_stat_user_indexes
                WHERE
                    idx_scan = 0
                ORDER BY
                    relname,
                    indexrelname;
            """)
            
            results = cur.fetchall()
            unused_indexes = []
            
            for row in results:
                table_name, index_name, times_used, index_size = row
                unused_indexes.append({
                    'database': 'postgresql',
                    'table_name': table_name,
                    'index_name': index_name,
                    'times_used': times_used,
                    'index_size': index_size,
                    'type': 'UNUSED_INDEX_CANDIDATE'
                })
            
            return unused_indexes
            
    except Exception as e:
        print(f"Error querying PostgreSQL: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def find_mysql_unused_indexes() -> List[Dict[str, Any]]:
    """
    Find unused indexes in MySQL using sys.schema_unused_indexes.
    
    Returns:
        List of unused index dictionaries
    """
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        
        with conn.cursor(dictionary=True) as cur:
            # Query for unused indexes
            cur.execute("""
                SELECT
                    object_schema AS db_name,
                    object_name AS table_name,
                    index_name
                FROM
                    sys.schema_unused_indexes;
            """)
            
            results = cur.fetchall()
            unused_indexes = []
            
            for row in results:
                db_name = row['db_name']
                table_name = row['table_name']
                index_name = row['index_name']
                
                unused_indexes.append({
                    'database': 'mysql',
                    'db_name': db_name,
                    'table_name': table_name,
                    'index_name': index_name,
                    'times_used': 0,  # sys.schema_unused_indexes doesn't provide scan count
                    'type': 'UNUSED_INDEX_CANDIDATE'
                })
            
            return unused_indexes
            
    except Exception as e:
        print(f"Error querying MySQL: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def generate_unused_index_recommendations(unused_indexes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate recommendations for unused indexes.
    
    Args:
        unused_indexes: List of unused index dictionaries
        
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
            'type': 'UNUSED_INDEX_CANDIDATE',
            'severity': 'MEDIUM',
            'rule_id': 'UNUSED_INDEX_001',
            'rationale': rationale,
            'suggested_action': f"DROP INDEX {idx['index_name']} ON {idx['table_name']};",
            'estimated_impact': 'Medium - Reduces storage overhead and improves write performance',
            'caveats': [
                "Please verify this index is not used for infrequent but important queries (e.g., annual reports) before dropping it.",
                "Consider monitoring the application for any performance degradation after removal.",
                "Backup the database before making schema changes."
            ],
            'evidence': {
                'database': idx['database'],
                'table_name': idx['table_name'],
                'index_name': idx['index_name'],
                'times_used': idx['times_used']
            }
        }
        
        recommendations.append(recommendation)
    
    return recommendations

def format_unused_index_report(recommendations: List[Dict[str, Any]]) -> str:
    """
    Format the unused index recommendations into a readable report.
    
    Args:
        recommendations: List of recommendation dictionaries
        
    Returns:
        Formatted report string
    """
    if not recommendations:
        return "--- 🆗 No unused indexes found. ---"
    
    output = []
    output.append("--- 🔍 Unused Index Analysis ---")
    output.append("")
    output.append(f"Found {len(recommendations)} potentially unused indexes:")
    output.append("")
    
    for i, rec in enumerate(recommendations, 1):
        output.append(f"Index #{i}: {rec['evidence']['index_name']} on {rec['evidence']['table_name']}")
        output.append(f"  Database: {rec['evidence']['database']}")
        output.append(f"  Times Used: {rec['evidence']['times_used']}")
        output.append(f"  Rationale: {rec['rationale']}")
        output.append(f"  Suggested Action: {rec['suggested_action']}")
        output.append(f"  Impact: {rec['estimated_impact']}")
        output.append("  Caveats:")
        for caveat in rec['caveats']:
            output.append(f"    - {caveat}")
        output.append("")
    
    return "\n".join(output)

def main():
    """Main function to run the unused index analysis."""
    print("--- Unused Index Analysis ---")
    print("Scanning both PostgreSQL and MySQL for unused indexes...")
    print()
    
    # Find unused indexes in both databases
    postgres_unused = find_postgres_unused_indexes()
    mysql_unused = find_mysql_unused_indexes()
    
    # Combine results
    all_unused = postgres_unused + mysql_unused
    
    print(f"PostgreSQL: Found {len(postgres_unused)} unused indexes")
    print(f"MySQL: Found {len(mysql_unused)} unused indexes")
    print(f"Total: {len(all_unused)} unused indexes")
    print()
    
    # Generate recommendations
    recommendations = generate_unused_index_recommendations(all_unused)
    
    # Format and display report
    report = format_unused_index_report(recommendations)
    print(report)
    
    # Save results to file
    results = {
        'unused_indexes': all_unused,
        'recommendations': recommendations,
        'summary': {
            'total_unused': len(all_unused),
            'postgres_count': len(postgres_unused),
            'mysql_count': len(mysql_unused)
        }
    }
    
    with open('artifacts/unused_indexes_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to: artifacts/unused_indexes_analysis.json")

if __name__ == '__main__':
    main()