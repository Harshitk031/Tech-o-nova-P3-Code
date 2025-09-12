#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

def test_imports():
    """Test all critical imports for the database analysis tool."""
    print("🧪 Testing Database Performance Analysis Tool Imports")
    print("=" * 50)
    
    # Test core database imports
    try:
        import psycopg2
        print("✅ psycopg2: PostgreSQL connectivity")
    except ImportError as e:
        print(f"❌ psycopg2: {e}")
    
    try:
        import mysql.connector
        print("✅ mysql.connector: MySQL connectivity")
    except ImportError as e:
        print(f"❌ mysql.connector: {e}")
    
    # Test SQL parsing
    try:
        from sqlglot import parse_one, exp
        print("✅ sqlglot: SQL parsing and analysis")
        
        # Test actual functionality
        parsed = parse_one("SELECT * FROM orders WHERE customer_id = 42;")
        where_clause = parsed.find(exp.Where)
        if where_clause:
            columns = [col.name for col in where_clause.find_all(exp.Column)]
            print(f"   → Successfully parsed WHERE clause: {columns}")
    except ImportError as e:
        print(f"❌ sqlglot: {e}")
    except Exception as e:
        print(f"⚠️  sqlglot: Imported but error in functionality: {e}")
    
    # Test optional imports
    try:
        import pandas
        print("✅ pandas: Data analysis")
    except ImportError:
        print("⚠️  pandas: Not installed (optional)")
    
    try:
        import numpy
        print("✅ numpy: Numerical computing")
    except ImportError:
        print("⚠️  numpy: Not installed (optional)")
    
    # Test project modules
    try:
        from src.analysis.sql_features import extract_sql_features
        print("✅ src.analysis.sql_features: Project module")
        
        # Test functionality
        result = extract_sql_features("SELECT * FROM orders WHERE customer_id = 42;")
        print(f"   → Successfully extracted features: {result}")
    except ImportError as e:
        print(f"❌ src.analysis.sql_features: {e}")
    except Exception as e:
        print(f"⚠️  src.analysis.sql_features: Imported but error: {e}")
    
    try:
        from src.analysis.scoring import calculate_scores
        print("✅ src.analysis.scoring: Project module")
    except ImportError as e:
        print(f"❌ src.analysis.scoring: {e}")
    except Exception as e:
        print(f"⚠️  src.analysis.scoring: Imported but error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Import test completed!")

if __name__ == '__main__':
    test_imports()
