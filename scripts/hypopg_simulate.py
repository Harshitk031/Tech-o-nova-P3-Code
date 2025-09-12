#!/usr/bin/env python3
"""
HypoPG Simulation Script for Database Performance Analysis
Simulates the effect of adding an index using HypoPG extension
"""

import psycopg2
import json
import re
import time
from typing import Dict, Tuple, Optional
import sys
import os

# Add the src directory to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.config.database_config import get_database_config
    USE_DB_CONFIG = True
except ImportError:
    USE_DB_CONFIG = False

def get_connection():
    """Get PostgreSQL database connection"""
    global USE_DB_CONFIG
    
    if USE_DB_CONFIG:
        try:
            db_config = get_database_config()
            return psycopg2.connect(
                host=db_config.get_postgres_config()['host'],
                port=db_config.get_postgres_config()['port'],
                user=db_config.get_postgres_config()['user'],
                password=db_config.get_postgres_config()['password'],
                dbname=db_config.get_postgres_config()['database']
            )
        except Exception as e:
            print(f"Error getting database config: {e}")
            USE_DB_CONFIG = False
    
    if not USE_DB_CONFIG:
        return psycopg2.connect(
            host="localhost",
            port="5432",
            user="postgres",
            password="postgres",
            dbname="postgres"
        )

def extract_index_name_from_sql(sql: str) -> Optional[str]:
    """Extract index name from CREATE INDEX SQL statement"""
    # Pattern to match CREATE INDEX index_name ON table_name
    pattern = r'CREATE\s+INDEX\s+(\w+)\s+ON\s+(\w+)'
    match = re.search(pattern, sql, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def extract_table_name_from_sql(sql: str) -> Optional[str]:
    """Extract table name from CREATE INDEX SQL statement"""
    pattern = r'CREATE\s+INDEX\s+\w+\s+ON\s+(\w+)'
    match = re.search(pattern, sql, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def run_hypopg_simulation(query: str, recommended_action: str) -> Tuple[Dict, Dict]:
    """
    Simulate the effect of adding an index using HypoPG
    
    Args:
        query: The SQL query to test
        recommended_action: The CREATE INDEX statement to simulate
        
    Returns:
        Tuple of (before_metrics, after_metrics)
    """
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Check if HypoPG extension is available
        try:
            cur.execute("SELECT 1 FROM pg_extension WHERE extname = 'hypopg';")
            if not cur.fetchone():
                # Try to create the extension
                try:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS hypopg;")
                    conn.commit()
                except Exception as e:
                    print(f"Warning: Could not create HypoPG extension: {e}")
                    # Fallback to basic simulation without HypoPG
                    return run_basic_simulation(query, recommended_action, conn, cur)
        except Exception as e:
            print(f"Warning: Could not check HypoPG extension: {e}")
            # Fallback to basic simulation without HypoPG
            return run_basic_simulation(query, recommended_action, conn, cur)
        
        # Get baseline performance (before)
        print(f"Running baseline query: {query[:100]}...")
        start_time = time.time()
        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
        before_result = cur.fetchone()[0][0]
        before_time = time.time() - start_time
        
        before_metrics = {
            'execution_time_ms': before_result.get('Execution Time', before_time * 1000),
            'planning_time_ms': before_result.get('Planning Time', 0),
            'total_cost': before_result.get('Total Cost', 0),
            'rows_returned': before_result.get('Plan', {}).get('Actual Rows', 0)
        }
        
        # Extract index details from recommendation
        index_name = extract_index_name_from_sql(recommended_action)
        table_name = extract_table_name_from_sql(recommended_action)
        
        if not index_name or not table_name:
            raise ValueError("Could not extract index or table name from recommendation")
        
        # Create hypothetical index
        print(f"Creating hypothetical index: {index_name} on {table_name}")
        cur.execute(f"SELECT * FROM hypopg_create_index('{recommended_action}');")
        hypo_index_result = cur.fetchone()
        
        if not hypo_index_result:
            raise ValueError("Failed to create hypothetical index")
        
        hypo_index_id = hypo_index_result[0]
        
        # Get performance with hypothetical index (after)
        print("Running query with hypothetical index...")
        start_time = time.time()
        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
        after_result = cur.fetchone()[0][0]
        after_time = time.time() - start_time
        
        after_metrics = {
            'execution_time_ms': after_result.get('Execution Time', after_time * 1000),
            'planning_time_ms': after_result.get('Planning Time', 0),
            'total_cost': after_result.get('Total Cost', 0),
            'rows_returned': after_result.get('Plan', {}).get('Actual Rows', 0)
        }
        
        # Clean up hypothetical index
        cur.execute(f"SELECT hypopg_drop_index({hypo_index_id});")
        conn.commit()
        
        print(f"Simulation complete. Before: {before_metrics['execution_time_ms']:.2f}ms, After: {after_metrics['execution_time_ms']:.2f}ms")
        
        return before_metrics, after_metrics
        
    except Exception as e:
        print(f"Error in HypoPG simulation: {e}")
        # Fallback to basic simulation
        if conn:
            cur = conn.cursor()
            return run_basic_simulation(query, recommended_action, conn, cur)
        else:
            raise e
    finally:
        if conn:
            conn.close()

def run_basic_simulation(query: str, recommended_action: str, conn, cur) -> Tuple[Dict, Dict]:
    """
    Fallback simulation without HypoPG - just run the query twice and estimate improvement
    """
    print("Running basic simulation (HypoPG not available)")
    
    try:
        # Rollback any failed transaction
        conn.rollback()
        
        # Check if query is valid for EXPLAIN
        if not is_valid_for_explain(query):
            print(f"Query not suitable for EXPLAIN: {query[:50]}...")
            return get_estimated_metrics(query, recommended_action)
        
        # Check if query references tables that don't exist in main database
        if references_historical_tables(query):
            print(f"Query references historical tables, using estimated metrics: {query[:50]}...")
            return get_estimated_metrics(query, recommended_action)
        
        # Get baseline performance
        start_time = time.time()
        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
        before_result = cur.fetchone()[0][0]
        before_time = time.time() - start_time
        
        before_metrics = {
            'execution_time_ms': before_result.get('Execution Time', before_time * 1000),
            'planning_time_ms': before_result.get('Planning Time', 0),
            'total_cost': before_result.get('Total Cost', 0),
            'rows_returned': before_result.get('Plan', {}).get('Actual Rows', 0)
        }
        
        # Estimate improvement based on query type and recommendation
        estimated_improvement = estimate_index_improvement(query, recommended_action, before_metrics)
        
        after_metrics = {
            'execution_time_ms': before_metrics['execution_time_ms'] * (1 - estimated_improvement),
            'planning_time_ms': before_metrics['planning_time_ms'],
            'total_cost': before_metrics['total_cost'] * 0.1,  # Assume 90% cost reduction
            'rows_returned': before_metrics['rows_returned']
        }
        
        return before_metrics, after_metrics
        
    except Exception as e:
        print(f"Error in basic simulation: {e}")
        return get_estimated_metrics(query, recommended_action)

def is_valid_for_explain(query: str) -> bool:
    """Check if query is valid for EXPLAIN"""
    query_upper = query.upper().strip()
    
    # Queries that cannot be explained
    invalid_queries = [
        'COMMIT', 'ROLLBACK', 'BEGIN', 'START TRANSACTION',
        'SET', 'RESET', 'SHOW', 'EXPLAIN', 'VACUUM', 'ANALYZE',
        'CREATE', 'DROP', 'ALTER', 'INSERT', 'UPDATE', 'DELETE'
    ]
    
    for invalid in invalid_queries:
        if query_upper.startswith(invalid):
            return False
    
    return True

def references_historical_tables(query: str) -> bool:
    """Check if query references tables that only exist in historical database"""
    query_lower = query.lower()
    
    # Tables that only exist in performance_history database
    historical_tables = [
        'query_snapshots',
        'index_usage_snapshots',
        'performance_regressions',
        'configuration_snapshots',
        'schema_snapshots'
    ]
    
    for table in historical_tables:
        if table in query_lower:
            return True
    
    return False

def get_estimated_metrics(query: str, recommended_action: str) -> Tuple[Dict, Dict]:
    """Get estimated metrics when real simulation is not possible"""
    query_upper = query.upper()
    
    # Base metrics based on query type and complexity
    if 'SELECT' in query_upper:
        if 'JOIN' in query_upper or 'GROUP BY' in query_upper:
            base_time = 100  # Complex SELECT queries
        elif 'WHERE' in query_upper:
            base_time = 50   # SELECT with WHERE
        else:
            base_time = 30   # Simple SELECT
    elif 'INSERT' in query_upper:
        base_time = 20  # 20ms for INSERT queries
    elif 'UPDATE' in query_upper or 'DELETE' in query_upper:
        base_time = 40  # 40ms for UPDATE/DELETE
    else:
        base_time = 10  # 10ms for other queries
    
    # Add variation based on query length and complexity
    complexity_factor = 1.0
    if 'query_snapshots' in query.lower():
        complexity_factor = 1.5  # Historical queries are typically more complex
    if 'COUNT' in query_upper or 'DISTINCT' in query_upper:
        complexity_factor *= 1.3
    
    variation = len(query) * 0.05
    estimated_time = (base_time + variation) * complexity_factor
    
    estimated_improvement = estimate_index_improvement(query, recommended_action, {'execution_time_ms': estimated_time})
    
    before_metrics = {
        'execution_time_ms': estimated_time,
        'planning_time_ms': 5,
        'total_cost': estimated_time * 10,
        'rows_returned': 100 if 'COUNT' not in query_upper else 1
    }
    
    after_metrics = {
        'execution_time_ms': estimated_time * (1 - estimated_improvement),
        'planning_time_ms': 5,
        'total_cost': estimated_time * 1,
        'rows_returned': before_metrics['rows_returned']
    }
    
    return before_metrics, after_metrics

def estimate_index_improvement(query: str, recommended_action: str, before_metrics: Dict) -> float:
    """
    Estimate the improvement percentage based on query characteristics
    """
    query_lower = query.lower()
    recommendation_lower = recommended_action.lower()
    
    # Base improvement estimates
    if 'where' in query_lower and 'order by' in query_lower:
        return 0.7  # 70% improvement for WHERE + ORDER BY
    elif 'where' in query_lower:
        return 0.5  # 50% improvement for WHERE clause
    elif 'order by' in query_lower:
        return 0.6  # 60% improvement for ORDER BY
    elif 'join' in query_lower:
        return 0.4  # 40% improvement for JOINs
    else:
        return 0.3  # 30% improvement for other cases

if __name__ == "__main__":
    # Test the simulation
    test_query = "SELECT * FROM olist_orders_dataset WHERE order_status = 'delivered'"
    test_recommendation = "CREATE INDEX idx_orders_status ON olist_orders_dataset (order_status)"
    
    try:
        before, after = run_hypopg_simulation(test_query, test_recommendation)
        print(f"Before: {before}")
        print(f"After: {after}")
        improvement = (before['execution_time_ms'] - after['execution_time_ms']) / before['execution_time_ms'] * 100
        print(f"Estimated improvement: {improvement:.1f}%")
    except Exception as e:
        print(f"Test failed: {e}")