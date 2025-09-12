#!/usr/bin/env python3
"""
Installation Verification Script
Verifies that all required dependencies are properly installed.
"""

import sys
import importlib

def check_dependency(module_name, package_name=None):
    """Check if a dependency is installed and importable."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name}: Available")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name}: Missing - {e}")
        return False

def main():
    """Verify all required dependencies."""
    print("🔍 Verifying Database Performance Analysis Tool Dependencies")
    print("=" * 60)
    
    # Core dependencies
    core_deps = [
        ("psycopg2", "PostgreSQL connectivity"),
        ("mysql.connector", "MySQL connectivity"),
        ("sqlglot", "SQL parsing"),
        ("json", "JSON handling"),
        ("typing", "Type hints")
    ]
    
    print("\n📦 Core Dependencies:")
    core_success = 0
    for module, name in core_deps:
        if check_dependency(module, name):
            core_success += 1
    
    # Optional dependencies
    optional_deps = [
        ("pandas", "Data analysis"),
        ("numpy", "Numerical computing"),
        ("colorama", "Colored terminal output"),
        ("tqdm", "Progress bars"),
        ("yaml", "YAML configuration"),
        ("click", "Enhanced CLI")
    ]
    
    print("\n🔧 Optional Dependencies:")
    optional_success = 0
    for module, name in optional_deps:
        if check_dependency(module, name):
            optional_success += 1
    
    # Development dependencies
    dev_deps = [
        ("pytest", "Testing framework"),
        ("black", "Code formatting"),
        ("flake8", "Code linting"),
        ("sphinx", "Documentation")
    ]
    
    print("\n🛠️  Development Dependencies:")
    dev_success = 0
    for module, name in dev_deps:
        if check_dependency(module, name):
            dev_success += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Installation Summary:")
    print(f"  Core Dependencies: {core_success}/{len(core_deps)} installed")
    print(f"  Optional Dependencies: {optional_success}/{len(optional_deps)} installed")
    print(f"  Development Dependencies: {dev_success}/{len(dev_deps)} installed")
    
    # Test database connections
    print("\n🔌 Testing Database Connections:")
    
    # Test PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432")
        conn.close()
        print("✅ PostgreSQL: Connection successful")
    except Exception as e:
        print(f"❌ PostgreSQL: Connection failed - {e}")
    
    # Test MySQL
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='mysql',
            database='test'
        )
        conn.close()
        print("✅ MySQL: Connection successful")
    except Exception as e:
        print(f"❌ MySQL: Connection failed - {e}")
    
    # Test tool functionality
    print("\n🧪 Testing Tool Functionality:")
    try:
        from src.analysis.sql_features import extract_sql_features
        result = extract_sql_features("SELECT * FROM orders WHERE customer_id = 42;")
        print("✅ SQL Feature Extraction: Working")
    except Exception as e:
        print(f"❌ SQL Feature Extraction: Failed - {e}")
    
    try:
        from src.analysis.scoring import calculate_scores
        print("✅ Scoring System: Working")
    except Exception as e:
        print(f"❌ Scoring System: Failed - {e}")
    
    # Final assessment
    print("\n" + "=" * 60)
    if core_success == len(core_deps):
        print("🎉 Installation verification PASSED!")
        print("   All core dependencies are installed and working.")
        print("   The Database Performance Analysis Tool is ready to use.")
    else:
        print("⚠️  Installation verification PARTIAL")
        print("   Some core dependencies are missing.")
        print("   Run: pip install -r requirements-minimal.txt")
    
    if optional_success > 0:
        print(f"   Optional features available: {optional_success}/{len(optional_deps)}")
    
    print("\n📚 Next Steps:")
    print("   1. Start databases: docker-compose up -d")
    print("   2. Run analysis: python analyze_db.py postgres \"SELECT * FROM orders WHERE customer_id = 42;\"")
    print("   3. See help: python analyze_db.py --help")

if __name__ == '__main__':
    main()
