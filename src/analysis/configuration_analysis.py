#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Configuration Analysis Module
Analyzes database configuration and schema for optimization opportunities.
"""

import psycopg2
import mysql.connector
import sys
import os
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.database_config import get_database_config

class ConfigurationAnalyzer:
    """Analyzes database configuration for optimization opportunities."""
    
    def __init__(self):
        """Initialize the configuration analyzer."""
        self.db_config = get_database_config()
        self.postgres_conn_str = self.db_config.get_postgres_connection_string()
        self.mysql_config = self.db_config.get_mysql_config()
    
    def analyze_postgresql_configuration(self) -> Dict[str, Any]:
        """Analyze PostgreSQL configuration settings."""
        try:
            with psycopg2.connect(self.postgres_conn_str) as conn:
                with conn.cursor() as cur:
                    # Get key configuration settings
                    config_query = """
                    SELECT 
                        name,
                        setting,
                        unit,
                        context,
                        short_desc
                    FROM pg_settings
                    WHERE name IN (
                        'shared_buffers', 'work_mem', 'maintenance_work_mem',
                        'effective_cache_size', 'random_page_cost', 'seq_page_cost',
                        'checkpoint_completion_target', 'wal_buffers', 'max_connections',
                        'shared_preload_libraries', 'log_statement', 'log_min_duration_statement',
                        'autovacuum', 'default_statistics_target'
                    )
                    ORDER BY name
                    """
                    
                    cur.execute(config_query)
                    settings = {}
                    for row in cur.fetchall():
                        name, setting, unit, context, desc = row
                        settings[name] = {
                            'value': setting,
                            'unit': unit,
                            'context': context,
                            'description': desc
                        }
                    
                    # Analyze configuration
                    recommendations = self._analyze_postgres_settings(settings)
                    
                    return {
                        'database_type': 'postgresql',
                        'settings': settings,
                        'recommendations': recommendations,
                        'analyzed_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            return {
                'database_type': 'postgresql',
                'error': f'Failed to analyze PostgreSQL configuration: {str(e)}',
                'analyzed_at': datetime.now().isoformat()
            }
    
    def analyze_mysql_configuration(self) -> Dict[str, Any]:
        """Analyze MySQL configuration settings."""
        try:
            with mysql.connector.connect(**self.mysql_config) as conn:
                with conn.cursor(dictionary=True) as cur:
                    # Get key configuration variables
                    config_query = """
                    SHOW VARIABLES WHERE Variable_name IN (
                        'innodb_buffer_pool_size', 'innodb_log_file_size', 'innodb_log_buffer_size',
                        'query_cache_size', 'query_cache_type', 'max_connections',
                        'slow_query_log', 'long_query_time', 'innodb_flush_method'
                    )
                    ORDER BY Variable_name
                    """
                    
                    cur.execute(config_query)
                    settings = {}
                    for row in cur.fetchall():
                        settings[row['Variable_name']] = {
                            'value': row['Value'],
                            'description': 'MySQL configuration variable'
                        }
                    
                    # Analyze configuration
                    recommendations = self._analyze_mysql_settings(settings)
                    
                    return {
                        'database_type': 'mysql',
                        'settings': settings,
                        'recommendations': recommendations,
                        'analyzed_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            return {
                'database_type': 'mysql',
                'error': f'Failed to analyze MySQL configuration: {str(e)}',
                'analyzed_at': datetime.now().isoformat()
            }
    
    def _analyze_postgres_settings(self, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze PostgreSQL settings and generate recommendations."""
        recommendations = []
        
        # Check shared_buffers
        shared_buffers = self._parse_size(settings.get('shared_buffers', {}).get('value', '0'))
        if shared_buffers < 256 * 1024 * 1024:  # Less than 256MB
            recommendations.append({
                'setting': 'shared_buffers',
                'current_value': settings.get('shared_buffers', {}).get('value', 'unknown'),
                'issue': 'Low shared_buffers',
                'recommendation': 'Increase shared_buffers to 25% of RAM (minimum 256MB)',
                'severity': 'HIGH',
                'impact': 'Improves buffer hit ratio and reduces I/O'
            })
        
        # Check work_mem
        work_mem = self._parse_size(settings.get('work_mem', {}).get('value', '0'))
        if work_mem < 4 * 1024 * 1024:  # Less than 4MB
            recommendations.append({
                'setting': 'work_mem',
                'current_value': settings.get('work_mem', {}).get('value', 'unknown'),
                'issue': 'Low work_mem',
                'recommendation': 'Increase work_mem to 4-16MB for better sort/hash operations',
                'severity': 'MEDIUM',
                'impact': 'Improves sort and hash join performance'
            })
        
        # Check autovacuum
        autovacuum = settings.get('autovacuum', {}).get('value', 'on')
        if autovacuum.lower() != 'on':
            recommendations.append({
                'setting': 'autovacuum',
                'current_value': settings.get('autovacuum', {}).get('value', 'unknown'),
                'issue': 'Autovacuum disabled',
                'recommendation': 'Enable autovacuum for table maintenance',
                'severity': 'HIGH',
                'impact': 'Prevents table bloat and maintains statistics'
            })
        
        return recommendations
    
    def _analyze_mysql_settings(self, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze MySQL settings and generate recommendations."""
        recommendations = []
        
        # Check InnoDB buffer pool size
        innodb_buffer_pool = self._parse_size(settings.get('innodb_buffer_pool_size', {}).get('value', '0'))
        if innodb_buffer_pool < 128 * 1024 * 1024:  # Less than 128MB
            recommendations.append({
                'setting': 'innodb_buffer_pool_size',
                'current_value': settings.get('innodb_buffer_pool_size', {}).get('value', 'unknown'),
                'issue': 'Low InnoDB buffer pool size',
                'recommendation': 'Increase innodb_buffer_pool_size to 70-80% of RAM',
                'severity': 'HIGH',
                'impact': 'Improves InnoDB performance significantly'
            })
        
        # Check slow query log
        slow_query_log = settings.get('slow_query_log', {}).get('value', 'OFF')
        if slow_query_log == 'OFF':
            recommendations.append({
                'setting': 'slow_query_log',
                'current_value': 'Disabled',
                'issue': 'Slow query logging disabled',
                'recommendation': 'Enable slow query logging for performance monitoring',
                'severity': 'LOW',
                'impact': 'Enables identification of slow queries'
            })
        
        return recommendations
    
    def _parse_size(self, size_str: str) -> int:
        """Parse size string (e.g., '128MB', '1GB') to bytes."""
        if not size_str or size_str == '0':
            return 0
        
        size_str = size_str.upper().strip()
        
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                try:
                    number = float(size_str[:-len(suffix)])
                    return int(number * multiplier)
                except ValueError:
                    pass
        
        # Try to parse as plain number (assume bytes)
        try:
            return int(float(size_str))
        except ValueError:
            return 0

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze database configuration")
    parser.add_argument('--database', choices=['postgresql', 'mysql', 'both'], default='both', help='Database to analyze')
    parser.add_argument('--output', help='Output file for JSON results')
    
    args = parser.parse_args()
    
    analyzer = ConfigurationAnalyzer()
    
    try:
        results = {}
        
        if args.database in ['postgresql', 'both']:
            print("Analyzing PostgreSQL configuration...")
            results['postgresql'] = analyzer.analyze_postgresql_configuration()
        
        if args.database in ['mysql', 'both']:
            print("Analyzing MySQL configuration...")
            results['mysql'] = analyzer.analyze_mysql_configuration()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to: {args.output}")
        else:
            print(json.dumps(results, indent=2))
            
    except KeyboardInterrupt:
        print("\nAnalysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
