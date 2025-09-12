#!/usr/bin/env python3
"""
Historical Data Analysis and Trending Script
Analyzes collected performance data to identify trends and patterns.
"""

import psycopg2
import sys
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database_config import get_database_config

class PerformanceTrendAnalyzer:
    """Analyzes historical performance data for trends and patterns."""
    
    def __init__(self, historical_db_name: str = "performance_history"):
        """Initialize the analyzer."""
        self.historical_db_name = historical_db_name
        self.db_config = get_database_config()
        
        # PostgreSQL connection for historical data
        self.historical_conn_str = self.db_config.get_postgres_connection_string().replace(
            f"/{self.db_config.get_postgres_config()['database']}", 
            f"/{historical_db_name}"
        )
    
    def get_query_performance_trends(self, hours: int = 24, limit: int = 20) -> List[Dict[str, Any]]:
        """Get query performance trends over time."""
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    query = """
                    SELECT 
                        database_name,
                        query_id,
                        query_text,
                        hour_bucket,
                        snapshot_count,
                        avg_exec_time_ms,
                        max_exec_time_ms,
                        min_exec_time_ms,
                        total_calls,
                        avg_mean_exec_time_ms
                    FROM query_performance_trends
                    WHERE hour_bucket >= NOW() - INTERVAL '%s hours'
                    ORDER BY hour_bucket DESC, avg_exec_time_ms DESC
                    LIMIT %s
                    """
                    
                    cur.execute(query, (hours, limit))
                    columns = [desc[0] for desc in cur.description]
                    results = []
                    
                    for row in cur.fetchall():
                        result = dict(zip(columns, row))
                        results.append(result)
                    
                    return results
                    
        except Exception as e:
            print(f"Error getting query performance trends: {e}")
            return []
    
    def get_slowest_queries(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the slowest queries over time."""
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    query = """
                    SELECT 
                        database_name,
                        query_text,
                        AVG(total_exec_time_ms) as avg_total_time,
                        MAX(total_exec_time_ms) as max_total_time,
                        SUM(calls) as total_calls,
                        COUNT(*) as snapshot_count
                    FROM query_snapshots
                    WHERE captured_at >= NOW() - INTERVAL '%s hours'
                    GROUP BY database_name, query_text
                    ORDER BY avg_total_time DESC
                    LIMIT %s
                    """
                    
                    cur.execute(query, (hours, limit))
                    columns = [desc[0] for desc in cur.description]
                    results = []
                    
                    for row in cur.fetchall():
                        result = dict(zip(columns, row))
                        results.append(result)
                    
                    return results
                    
        except Exception as e:
            print(f"Error getting slowest queries: {e}")
            return []
    
    def get_index_usage_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get index usage trends over time."""
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    query = """
                    SELECT 
                        database_name,
                        table_name,
                        index_name,
                        hour_bucket,
                        avg_times_used,
                        max_times_used,
                        min_times_used,
                        avg_index_size_kb
                    FROM index_usage_trends
                    WHERE hour_bucket >= NOW() - INTERVAL '%s hours'
                    ORDER BY hour_bucket DESC, avg_times_used DESC
                    """
                    
                    cur.execute(query, (hours,))
                    columns = [desc[0] for desc in cur.description]
                    results = []
                    
                    for row in cur.fetchall():
                        result = dict(zip(columns, row))
                        results.append(result)
                    
                    return results
                    
        except Exception as e:
            print(f"Error getting index usage trends: {e}")
            return []
    
    def get_unused_indexes(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get indexes that haven't been used recently."""
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    query = """
                    SELECT 
                        database_name,
                        table_name,
                        index_name,
                        AVG(times_used) as avg_times_used,
                        MAX(times_used) as max_times_used,
                        AVG(index_size_kb) as avg_size_kb,
                        COUNT(*) as snapshot_count
                    FROM index_usage_snapshots
                    WHERE captured_at >= NOW() - INTERVAL '%s days'
                    GROUP BY database_name, table_name, index_name
                    HAVING AVG(times_used) < 1
                    ORDER BY avg_size_kb DESC
                    """
                    
                    cur.execute(query, (days,))
                    columns = [desc[0] for desc in cur.description]
                    results = []
                    
                    for row in cur.fetchall():
                        result = dict(zip(columns, row))
                        results.append(result)
                    
                    return results
                    
        except Exception as e:
            print(f"Error getting unused indexes: {e}")
            return []
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get overall performance summary."""
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    # Get query performance summary
                    query_summary = """
                    SELECT 
                        COUNT(DISTINCT query_id) as unique_queries,
                        SUM(calls) as total_calls,
                        AVG(total_exec_time_ms) as avg_exec_time,
                        MAX(total_exec_time_ms) as max_exec_time,
                        COUNT(*) as total_snapshots
                    FROM query_snapshots
                    WHERE captured_at >= NOW() - INTERVAL '%s hours'
                    """
                    
                    cur.execute(query_summary, (hours,))
                    query_stats = dict(zip([desc[0] for desc in cur.description], cur.fetchone()))
                    
                    # Get index usage summary
                    index_summary = """
                    SELECT 
                        COUNT(DISTINCT CONCAT(table_name, '.', index_name)) as unique_indexes,
                        AVG(times_used) as avg_usage,
                        COUNT(*) as total_index_snapshots
                    FROM index_usage_snapshots
                    WHERE captured_at >= NOW() - INTERVAL '%s hours'
                    """
                    
                    cur.execute(index_summary, (hours,))
                    index_stats = dict(zip([desc[0] for desc in cur.description], cur.fetchone()))
                    
                    return {
                        'query_performance': query_stats,
                        'index_usage': index_stats,
                        'analysis_period_hours': hours,
                        'generated_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            print(f"Error getting performance summary: {e}")
            return {}
    
    def generate_trend_report(self, hours: int = 24) -> str:
        """Generate a comprehensive trend report."""
        report = []
        report.append("=" * 80)
        report.append("📊 DATABASE PERFORMANCE TREND ANALYSIS")
        report.append("=" * 80)
        report.append(f"Analysis Period: Last {hours} hours")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Performance summary
        summary = self.get_performance_summary(hours)
        if summary:
            report.append("📈 PERFORMANCE SUMMARY")
            report.append("-" * 40)
            query_perf = summary.get('query_performance', {})
            report.append(f"Unique Queries: {query_perf.get('unique_queries', 0)}")
            report.append(f"Total Calls: {query_perf.get('total_calls', 0):,}")
            report.append(f"Average Execution Time: {query_perf.get('avg_exec_time', 0):.2f} ms")
            report.append(f"Maximum Execution Time: {query_perf.get('max_exec_time', 0):.2f} ms")
            report.append("")
            
            index_usage = summary.get('index_usage', {})
            report.append(f"Unique Indexes: {index_usage.get('unique_indexes', 0)}")
            report.append(f"Average Index Usage: {index_usage.get('avg_usage', 0):.2f}")
            report.append("")
        
        # Slowest queries
        slowest_queries = self.get_slowest_queries(hours, 5)
        if slowest_queries:
            report.append("🐌 SLOWEST QUERIES")
            report.append("-" * 40)
            for i, query in enumerate(slowest_queries, 1):
                report.append(f"{i}. {query['database_name']} - {query['avg_total_time']:.2f} ms avg")
                report.append(f"   Calls: {query['total_calls']:,}")
                report.append(f"   Query: {query['query_text'][:100]}...")
                report.append("")
        
        # Unused indexes
        unused_indexes = self.get_unused_indexes(7)
        if unused_indexes:
            report.append("🗑️  POTENTIALLY UNUSED INDEXES")
            report.append("-" * 40)
            for i, index in enumerate(unused_indexes[:5], 1):
                report.append(f"{i}. {index['database_name']}.{index['table_name']}.{index['index_name']}")
                report.append(f"   Usage: {index['avg_times_used']:.2f} times")
                report.append(f"   Size: {index['avg_size_kb']:.2f} KB")
                report.append("")
        
        return "\n".join(report)
    
    def export_trends_to_json(self, hours: int = 24, output_file: str = None) -> str:
        """Export trend data to JSON file."""
        if not output_file:
            output_file = f"trends_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'summary': self.get_performance_summary(hours),
            'slowest_queries': self.get_slowest_queries(hours, 20),
            'unused_indexes': self.get_unused_indexes(7),
            'query_trends': self.get_query_performance_trends(hours, 50),
            'index_trends': self.get_index_usage_trends(hours)
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        return output_file

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze database performance trends")
    parser.add_argument('--hours', type=int, default=24, help='Hours of data to analyze')
    parser.add_argument('--output', help='Output file for JSON export')
    parser.add_argument('--report', action='store_true', help='Generate text report')
    parser.add_argument('--historical-db', default='performance_history', help='Historical database name')
    
    args = parser.parse_args()
    
    analyzer = PerformanceTrendAnalyzer(args.historical_db)
    
    try:
        if args.report:
            report = analyzer.generate_trend_report(args.hours)
            print(report)
        
        if args.output:
            output_file = analyzer.export_trends_to_json(args.hours, args.output)
            print(f"📄 Trends exported to: {output_file}")
        
        if not args.report and not args.output:
            # Default: show summary
            summary = analyzer.get_performance_summary(args.hours)
            print(json.dumps(summary, indent=2, default=str))
            
    except KeyboardInterrupt:
        print("\n⏹️  Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
