#!/usr/bin/env python3
"""
MySQL Statistics Collection Script
Collects slow query log data and stores it in historical database.
"""

import mysql.connector
import psycopg2
import sys
import os
import json
import subprocess
import tempfile
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database_config import get_database_config, get_historical_postgres_connection_string

class MySQLStatsCollector:
    """Collects MySQL performance statistics."""
    
    def __init__(self, target_db_name: str = "test", historical_db_name: str = "performance_history"):
        """Initialize the collector."""
        self.target_db_name = target_db_name
        self.historical_db_name = historical_db_name
        self.db_config = get_database_config()
        
        # MySQL connection config
        self.mysql_config = self.db_config.get_mysql_config()
        self.mysql_config['database'] = target_db_name
        
        # PostgreSQL connection for historical storage
        self.historical_conn_str = get_historical_postgres_connection_string(historical_db_name)
    
    def collect_slow_query_stats(self) -> List[Dict[str, Any]]:
        """Collect slow query statistics from MySQL."""
        try:
            with mysql.connector.connect(**self.mysql_config) as conn:
                with conn.cursor(dictionary=True) as cur:
                    # Query performance_schema for slow queries
                    query = """
                    SELECT 
                        DIGEST_TEXT as query_fingerprint,
                        SQL_TEXT as query_sample,
                        COUNT_STAR as calls,
                        SUM_TIMER_WAIT / 1000000000000 as total_time_s,
                        AVG_TIMER_WAIT / 1000000000000 as avg_time_s,
                        MIN_TIMER_WAIT / 1000000000000 as min_time_s,
                        MAX_TIMER_WAIT / 1000000000000 as max_time_s,
                        SUM_ROWS_EXAMINED as rows_examined,
                        SUM_ROWS_SENT as rows_sent
                    FROM performance_schema.events_statements_summary_by_digest
                    WHERE COUNT_STAR > 0
                    ORDER BY SUM_TIMER_WAIT DESC
                    LIMIT 100
                    """
                    
                    cur.execute(query)
                    results = []
                    
                    for row in cur.fetchall():
                        row['database_name'] = self.target_db_name
                        results.append(row)
                    
                    return results
                    
        except Exception as e:
            print(f"Error collecting MySQL slow query stats: {e}")
            return []
    
    def collect_index_usage_stats(self) -> List[Dict[str, Any]]:
        """Collect index usage statistics from MySQL."""
        try:
            with mysql.connector.connect(**self.mysql_config) as conn:
                with conn.cursor(dictionary=True) as cur:
                    # Query sys.schema_unused_indexes for unused indexes
                    query = """
                    SELECT 
                        object_schema as schema_name,
                        object_name as table_name,
                        index_name,
                        0 as times_used,
                        'Unknown' as size_pretty,
                        0 as size_kb
                    FROM sys.schema_unused_indexes
                    WHERE object_schema = %s
                    """
                    
                    cur.execute(query, (self.target_db_name,))
                    results = []
                    
                    for row in cur.fetchall():
                        row['database_name'] = self.target_db_name
                        row['database_type'] = 'mysql'
                        results.append(row)
                    
                    # Also get used indexes from performance_schema
                    used_indexes_query = """
                    SELECT 
                        OBJECT_SCHEMA as schema_name,
                        OBJECT_NAME as table_name,
                        INDEX_NAME as index_name,
                        COUNT_FETCH + COUNT_INSERT + COUNT_UPDATE + COUNT_DELETE as times_used,
                        'Unknown' as size_pretty,
                        0 as size_kb
                    FROM performance_schema.table_io_waits_summary_by_index_usage
                    WHERE OBJECT_SCHEMA = %s
                    AND (COUNT_FETCH + COUNT_INSERT + COUNT_UPDATE + COUNT_DELETE) > 0
                    """
                    
                    cur.execute(used_indexes_query, (self.target_db_name,))
                    
                    for row in cur.fetchall():
                        row['database_name'] = self.target_db_name
                        row['database_type'] = 'mysql'
                        results.append(row)
                    
                    return results
                    
        except Exception as e:
            print(f"Error collecting MySQL index usage stats: {e}")
            return []
    
    def store_slow_log_summary(self, stats: List[Dict[str, Any]]) -> bool:
        """Store slow query statistics in historical database."""
        if not stats:
            return False
            
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    insert_query = """
                    INSERT INTO slow_log_summary (
                        database_name, query_fingerprint, query_sample, total_time_s,
                        calls, avg_time_s, min_time_s, max_time_s, rows_examined, rows_sent
                    ) VALUES (
                        %(database_name)s, %(query_fingerprint)s, %(query_sample)s,
                        %(total_time_s)s, %(calls)s, %(avg_time_s)s, %(min_time_s)s,
                        %(max_time_s)s, %(rows_examined)s, %(rows_sent)s
                    )
                    """
                    
                    cur.executemany(insert_query, stats)
                    conn.commit()
                    
                    print(f"✅ Stored {len(stats)} slow query summaries")
                    return True
                    
        except Exception as e:
            print(f"Error storing slow log summary: {e}")
            return False
    
    def store_index_usage_snapshots(self, stats: List[Dict[str, Any]]) -> bool:
        """Store index usage statistics in historical database."""
        if not stats:
            return False
            
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    insert_query = """
                    INSERT INTO index_usage_snapshots (
                        database_name, database_type, table_name, index_name,
                        times_used, index_size_kb
                    ) VALUES (
                        %(database_name)s, %(database_type)s, %(table_name)s,
                        %(index_name)s, %(times_used)s, %(size_kb)s
                    )
                    """
                    
                    cur.executemany(insert_query, stats)
                    conn.commit()
                    
                    print(f"✅ Stored {len(stats)} index usage snapshots")
                    return True
                    
        except Exception as e:
            print(f"Error storing index usage snapshots: {e}")
            return False
    
    def collect_and_store(self) -> bool:
        """Main method to collect and store all statistics."""
        print(f"🔍 Collecting MySQL statistics from {self.target_db_name}")
        print(f"📊 Storing in historical database: {self.historical_db_name}")
        
        # Collect slow query statistics
        slow_query_stats = self.collect_slow_query_stats()
        if slow_query_stats:
            self.store_slow_log_summary(slow_query_stats)
        
        # Collect index usage statistics
        index_stats = self.collect_index_usage_stats()
        if index_stats:
            self.store_index_usage_snapshots(index_stats)
        
        print(f"✅ Collection completed at {datetime.now()}")
        return True

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect MySQL performance statistics")
    parser.add_argument('--target-db', default='test', help='Target database name')
    parser.add_argument('--historical-db', default='performance_history', help='Historical database name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    collector = MySQLStatsCollector(args.target_db, args.historical_db)
    
    try:
        success = collector.collect_and_store()
        if success:
            print("🎉 MySQL statistics collection completed successfully")
            sys.exit(0)
        else:
            print("❌ Collection failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Collection cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
