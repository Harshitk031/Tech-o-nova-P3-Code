#!/usr/bin/env python3
"""
Database Schema Analysis Module
Analyzes database schema for anti-patterns and optimization opportunities.
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

class SchemaAnalyzer:
    """Analyzes database schema for anti-patterns and optimization opportunities."""
    
    def __init__(self):
        """Initialize the schema analyzer."""
        self.db_config = get_database_config()
        self.postgres_conn_str = self.db_config.get_postgres_connection_string()
        self.mysql_config = self.db_config.get_mysql_config()
    
    def analyze_postgresql_schema(self) -> Dict[str, Any]:
        """Analyze PostgreSQL schema for anti-patterns."""
        try:
            with psycopg2.connect(self.postgres_conn_str) as conn:
                with conn.cursor() as cur:
                    # Get table information
                    tables_query = """
                    SELECT 
                        schemaname,
                        tablename,
                        attname as column_name,
                        atttypid::regtype as data_type,
                        attnotnull as not_null,
                        attnum as column_position
                    FROM pg_tables t
                    JOIN pg_class c ON c.relname = t.tablename
                    JOIN pg_attribute a ON a.attrelid = c.oid
                    WHERE a.attnum > 0 AND NOT a.attisdropped
                    AND schemaname = 'public'
                    ORDER BY tablename, attnum
                    """
                    
                    cur.execute(tables_query)
                    tables = {}
                    for row in cur.fetchall():
                        schema, table, column, data_type, not_null, position = row
                        table_key = f"{schema}.{table}"
                        
                        if table_key not in tables:
                            tables[table_key] = {
                                'schema': schema,
                                'table': table,
                                'columns': []
                            }
                        
                        tables[table_key]['columns'].append({
                            'name': column,
                            'type': str(data_type),
                            'not_null': not_null,
                            'position': position
                        })
                    
                    # Analyze schema
                    recommendations = self._analyze_postgres_schema(tables)
                    
                    return {
                        'database_type': 'postgresql',
                        'tables': tables,
                        'recommendations': recommendations,
                        'analyzed_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            return {
                'database_type': 'postgresql',
                'error': f'Failed to analyze PostgreSQL schema: {str(e)}',
                'analyzed_at': datetime.now().isoformat()
            }
    
    def analyze_mysql_schema(self) -> Dict[str, Any]:
        """Analyze MySQL schema for anti-patterns."""
        try:
            with mysql.connector.connect(**self.mysql_config) as conn:
                with conn.cursor(dictionary=True) as cur:
                    # Get table information
                    tables_query = """
                    SELECT 
                        TABLE_SCHEMA as schema_name,
                        TABLE_NAME as table_name,
                        COLUMN_NAME as column_name,
                        DATA_TYPE as data_type,
                        IS_NULLABLE as is_nullable,
                        ORDINAL_POSITION as column_position
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                    ORDER BY TABLE_NAME, ORDINAL_POSITION
                    """
                    
                    cur.execute(tables_query)
                    tables = {}
                    for row in cur.fetchall():
                        table_key = f"{row['schema_name']}.{row['table_name']}"
                        
                        if table_key not in tables:
                            tables[table_key] = {
                                'schema': row['schema_name'],
                                'table': row['table_name'],
                                'columns': []
                            }
                        
                        tables[table_key]['columns'].append({
                            'name': row['column_name'],
                            'type': row['data_type'],
                            'is_nullable': row['is_nullable'] == 'YES',
                            'position': row['column_position']
                        })
                    
                    # Analyze schema
                    recommendations = self._analyze_mysql_schema(tables)
                    
                    return {
                        'database_type': 'mysql',
                        'tables': tables,
                        'recommendations': recommendations,
                        'analyzed_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            return {
                'database_type': 'mysql',
                'error': f'Failed to analyze MySQL schema: {str(e)}',
                'analyzed_at': datetime.now().isoformat()
            }
    
    def _analyze_postgres_schema(self, tables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze PostgreSQL schema for anti-patterns."""
        recommendations = []
        
        for table_key, table_info in tables.items():
            table_name = table_info['table']
            columns = table_info['columns']
            
            # Check for VARCHAR ID columns
            for column in columns:
                if (column['name'].lower() in ['id', 'uuid'] and 
                    'varchar' in column['type'].lower()):
                    recommendations.append({
                        'table': table_name,
                        'column': column['name'],
                        'issue': 'VARCHAR used for ID column',
                        'recommendation': f"Consider using INTEGER or UUID type for {column['name']}",
                        'severity': 'MEDIUM',
                        'impact': 'Improves performance and storage efficiency'
                    })
                
                # Check for TEXT columns without length limits
                if (column['type'].lower() == 'text' and 
                    column['name'].lower() not in ['description', 'content', 'body']):
                    recommendations.append({
                        'table': table_name,
                        'column': column['name'],
                        'issue': 'TEXT column may be oversized',
                        'recommendation': f"Consider VARCHAR with appropriate length for {column['name']}",
                        'severity': 'LOW',
                        'impact': 'Reduces storage overhead'
                    })
                
                # Check for missing NOT NULL constraints
                if (column['name'].lower() in ['id', 'created_at', 'updated_at'] and 
                    not column['not_null']):
                    recommendations.append({
                        'table': table_name,
                        'column': column['name'],
                        'issue': 'Missing NOT NULL constraint',
                        'recommendation': f"Add NOT NULL constraint to {column['name']}",
                        'severity': 'HIGH',
                        'impact': 'Ensures data integrity'
                    })
        
        return recommendations
    
    def _analyze_mysql_schema(self, tables: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze MySQL schema for anti-patterns."""
        recommendations = []
        
        for table_key, table_info in tables.items():
            table_name = table_info['table']
            columns = table_info['columns']
            
            # Check for VARCHAR ID columns
            for column in columns:
                if (column['name'].lower() in ['id', 'uuid'] and 
                    'varchar' in column['type'].lower()):
                    recommendations.append({
                        'table': table_name,
                        'column': column['name'],
                        'issue': 'VARCHAR used for ID column',
                        'recommendation': f"Consider using INT or CHAR(36) for {column['name']}",
                        'severity': 'MEDIUM',
                        'impact': 'Improves performance and storage efficiency'
                    })
                
                # Check for missing NOT NULL constraints
                if (column['name'].lower() in ['id', 'created_at', 'updated_at'] and 
                    column['is_nullable']):
                    recommendations.append({
                        'table': table_name,
                        'column': column['name'],
                        'issue': 'Missing NOT NULL constraint',
                        'recommendation': f"Add NOT NULL constraint to {column['name']}",
                        'severity': 'HIGH',
                        'impact': 'Ensures data integrity'
                    })
        
        return recommendations

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze database schema")
    parser.add_argument('--database', choices=['postgresql', 'mysql', 'both'], default='both', help='Database to analyze')
    parser.add_argument('--output', help='Output file for JSON results')
    
    args = parser.parse_args()
    
    analyzer = SchemaAnalyzer()
    
    try:
        results = {}
        
        if args.database in ['postgresql', 'both']:
            print("Analyzing PostgreSQL schema...")
            results['postgresql'] = analyzer.analyze_postgresql_schema()
        
        if args.database in ['mysql', 'both']:
            print("Analyzing MySQL schema...")
            results['mysql'] = analyzer.analyze_mysql_schema()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to: {args.output}")
        else:
            print(json.dumps(results, indent=2))
            
    except KeyboardInterrupt:
        print("\n⏹️  Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()