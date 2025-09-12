# src/analysis/sql_features.py
from sqlglot import parse_one, exp
from sqlglot.errors import ParseError
from typing import Dict, List, Optional

def extract_sql_features(sql_query: str) -> Dict[str, any]:
    """
    Parses a SQL query and extracts features like columns from the WHERE clause.
    
    Args:
        sql_query: The SQL query string to analyze
        
    Returns:
        Dictionary containing extracted features
        
    Raises:
        ValueError: If the query cannot be parsed or is invalid
    """
    if not sql_query or not sql_query.strip():
        raise ValueError("SQL query cannot be empty")
    
    try:
        # Parse the SQL query
        parsed = parse_one(sql_query.strip())
        
        if parsed is None:
            raise ValueError("No valid SQL expression found in query")
        
        # Extract features
        features = {
            'where_columns': [],
            'query_type': 'UNKNOWN',
            'table_name': None,
            'has_where_clause': False,
            'has_order_by': False,
            'has_group_by': False,
            'has_joins': False
        }
        
        # Determine query type
        if parsed.find(exp.Select):
            features['query_type'] = 'SELECT'
        elif parsed.find(exp.Insert):
            features['query_type'] = 'INSERT'
        elif parsed.find(exp.Update):
            features['query_type'] = 'UPDATE'
        elif parsed.find(exp.Delete):
            features['query_type'] = 'DELETE'
        
        # Extract table name (for simple queries)
        table = parsed.find(exp.Table)
        if table:
            features['table_name'] = table.name
        
        # Extract WHERE clause columns
        where_clause = parsed.find(exp.Where)
        if where_clause:
            features['has_where_clause'] = True
            for column in where_clause.find_all(exp.Column):
                if column.name not in features['where_columns']:
                    features['where_columns'].append(column.name)
        
        # Check for ORDER BY
        if parsed.find(exp.Order):
            features['has_order_by'] = True
        
        # Check for GROUP BY
        if parsed.find(exp.Group):
            features['has_group_by'] = True
        
        # Check for JOINs
        if parsed.find(exp.Join):
            features['has_joins'] = True
        
        print(f"--- SQL Feature Extraction ---")
        print(f"Original Query: {sql_query}")
        print(f"Query Type: {features['query_type']}")
        print(f"Table Name: {features['table_name']}")
        print(f"WHERE Columns: {features['where_columns']}")
        print(f"Has WHERE: {features['has_where_clause']}")
        print(f"Has ORDER BY: {features['has_order_by']}")
        print(f"Has GROUP BY: {features['has_group_by']}")
        print(f"Has JOINs: {features['has_joins']}")
        
        return features
        
    except ParseError as e:
        raise ValueError(f"Invalid SQL syntax: {e}")
    except Exception as e:
        raise ValueError(f"Error parsing SQL query: {e}")

if __name__ == '__main__':
    # This is the same query you've been testing
    query = "SELECT * FROM orders WHERE customer_id = 42;"
    extract_sql_features(query)
