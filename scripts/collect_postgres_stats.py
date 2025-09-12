#!/usr/bin/env python3
"""
PostgreSQL Statistics Collection Script
Collects query performance statistics from pg_stat_statements and stores them in historical database.
"""

import psycopg2
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database_config import get_database_config

class PostgreSQLStatsCollector:
    """Collects PostgreSQL performance statistics."""
    
    def __init__(self, target_db_name: str = "postgres", historical_db_name: str = "performance_history"):
        """Initialize the collector."""
        self.target_db_name = target_db_name
        self.historical_db_name = historical_db_name
        self.db_config = get_database_config()
        
        # Connection strings
        self.target_conn_str = self.db_config.get_postgres_connection_string().replace(
            f"/{self.db_config.get_postgres_config()['database']}", 
            f"/{target_db_name}"
        )
        self.historical_conn_str = self.db_config.get_postgres_connection_string().replace(
            f"/{self.db_config.get_postgres_config()['database']}", 
            f"/{historical_db_name}"
        )
    
    def collect_query_stats(self) -> List[Dict[str, Any]]:
        """Collect query statistics from pg_stat_statements."""
        try:
            with psycopg2.connect(self.target_conn_str) as conn:
                with conn.cursor() as cur:
                    # Query pg_stat_statements for performance data
                    query = """
                    SELECT 
                        queryid as query_id,
                        query as query_text,
                        calls,
                        total_exec_time as total_exec_time_ms,
                        mean_exec_time as mean_exec_time_ms,
                        rows,
                        shared_blks_hit,
                        shared_blks_read,
                        shared_blks_written,
                        local_blks_hit,
                        local_blks_read,
                        local_blks_written,
                        temp_blks_read,
                        temp_blks_written,
                        blk_read_time,
                        blk_write_time
                    FROM pg_stat_statements 
                    WHERE calls > 0
                    ORDER BY total_exec_time DESC
                    LIMIT 100
                    """
                    
                    cur.execute(query)
                    columns = [desc[0] for desc in cur.description]
                    results = []
                    
                    for row in cur.fetchall():
                        result = dict(zip(columns, row))
                        result['database_name'] = self.target_db_name
                        results.append(result)
                    
                    return results
                    
        except Exception as e:
            print(f"Error collecting PostgreSQL stats: {e}")
            return []
    
    def collect_index_usage_stats(self) -> List[Dict[str, Any]]:
        """Collect index usage statistics."""
        try:
            with psycopg2.connect(self.target_conn_str) as conn:
                with conn.cursor() as cur:
                    # Query pg_stat_user_indexes for index usage
                    query = """
                    SELECT 
                        schemaname as schema_name,
                        relname as table_name,
                        indexrelname as index_name,
                        idx_scan as times_used,
                        pg_size_pretty(pg_relation_size(indexrelid)) as size_pretty,
                        pg_relation_size(indexrelid) / 1024 as size_kb
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan ASC
                    """
                    
                    cur.execute(query)
                    columns = [desc[0] for desc in cur.description]
                    results = []
                    
                    for row in cur.fetchall():
                        result = dict(zip(columns, row))
                        result['database_name'] = self.target_db_name
                        result['database_type'] = 'postgresql'
                        results.append(result)
                    
                    return results
                    
        except Exception as e:
            print(f"Error collecting index usage stats: {e}")
            return []
    
    def store_query_snapshots(self, stats: List[Dict[str, Any]]) -> bool:
        """Store query statistics in historical database."""
        if not stats:
            return False
            
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    insert_query = """
                    INSERT INTO query_snapshots (
                        database_name, query_id, query_text, calls, total_exec_time_ms,
                        mean_exec_time_ms, rows, shared_blks_hit, shared_blks_read,
                        shared_blks_written, local_blks_hit, local_blks_read,
                        local_blks_written, temp_blks_read, temp_blks_written,
                        blk_read_time, blk_write_time
                    ) VALUES (
                        %(database_name)s, %(query_id)s, %(query_text)s, %(calls)s,
                        %(total_exec_time_ms)s, %(mean_exec_time_ms)s, %(rows)s,
                        %(shared_blks_hit)s, %(shared_blks_read)s, %(shared_blks_written)s,
                        %(local_blks_hit)s, %(local_blks_read)s, %(local_blks_written)s,
                        %(temp_blks_read)s, %(temp_blks_written)s, %(blk_read_time)s,
                        %(blk_write_time)s
                    )
                    """
                    
                    cur.executemany(insert_query, stats)
                    conn.commit()
                    
                    print(f"✅ Stored {len(stats)} query snapshots")
                    return True
                    
        except Exception as e:
            print(f"Error storing query snapshots: {e}")
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
        print(f"🔍 Collecting PostgreSQL statistics from {self.target_db_name}")
        print(f"📊 Storing in historical database: {self.historical_db_name}")
        
        # Collect query statistics
        query_stats = self.collect_query_stats()
        if query_stats:
            self.store_query_snapshots(query_stats)
        
        # Collect index usage statistics
        index_stats = self.collect_index_usage_stats()
        if index_stats:
            self.store_index_usage_snapshots(index_stats)
        
        print(f"✅ Collection completed at {datetime.now()}")
        return True

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Collect PostgreSQL performance statistics")
    parser.add_argument('--target-db', default='postgres', help='Target database name')
    parser.add_argument('--historical-db', default='performance_history', help='Historical database name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    collector = PostgreSQLStatsCollector(args.target_db, args.historical_db)
    
    try:
        success = collector.collect_and_store()
        if success:
            print("🎉 PostgreSQL statistics collection completed successfully")
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
