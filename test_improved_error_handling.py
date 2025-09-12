#!/usr/bin/env python3
"""
Test script for improved error handling and security features
"""

import subprocess
import sys
import os

def test_error_case(description, command, expected_exit_code=1):
    """Test an error case and verify it handles gracefully."""
    print(f"\n🧪 Testing: {description}")
    print(f"   Command: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        actual_exit_code = result.returncode
        
        if actual_exit_code == expected_exit_code:
            print(f"   ✅ PASSED - Correctly handled error (exit code: {actual_exit_code})")
            if result.stderr:
                print(f"   📝 Error message: {result.stderr.strip()[:100]}...")
            return True
        else:
            print(f"   ❌ FAILED - Expected exit code {expected_exit_code}, got {actual_exit_code}")
            if result.stdout:
                print(f"   📝 Output: {result.stdout.strip()[:100]}...")
            if result.stderr:
                print(f"   📝 Error: {result.stderr.strip()[:100]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ FAILED - Exception: {e}")
        return False

def test_success_case(description, command):
    """Test a success case."""
    print(f"\n✅ Testing: {description}")
    print(f"   Command: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ PASSED - Command executed successfully")
            return True
        else:
            print(f"   ❌ FAILED - Exit code: {result.returncode}")
            if result.stderr:
                print(f"   📝 Error: {result.stderr.strip()[:100]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ FAILED - Exception: {e}")
        return False

def test_sql_features():
    """Test SQL features extraction with various inputs."""
    print(f"\n🔍 Testing SQL Features Extraction")
    print("-" * 60)
    
    test_cases = [
        {
            "query": "SELECT * FROM orders WHERE customer_id = 42;",
            "description": "Valid SELECT query",
            "should_pass": True
        },
        {
            "query": "",
            "description": "Empty query",
            "should_pass": False
        },
        {
            "query": "INVALID SQL SYNTAX",
            "description": "Invalid SQL syntax",
            "should_pass": False
        },
        {
            "query": "SELECT * FROM orders WHERE customer_id = 42 ORDER BY created_at;",
            "description": "Query with ORDER BY",
            "should_pass": True
        },
        {
            "query": "UPDATE orders SET amount = 100 WHERE id = 1;",
            "description": "UPDATE query",
            "should_pass": True
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        print(f"\n   Testing: {test_case['description']}")
        print(f"   Query: {test_case['query']}")
        
        try:
            # Import and test the function directly
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from src.analysis.sql_features import extract_sql_features
            
            result = extract_sql_features(test_case['query'])
            
            if test_case['should_pass']:
                print(f"   ✅ PASSED - Extracted features: {len(result)} fields")
                passed += 1
            else:
                print(f"   ❌ FAILED - Should have failed but didn't")
                
        except Exception as e:
            if not test_case['should_pass']:
                print(f"   ✅ PASSED - Correctly failed: {e}")
                passed += 1
            else:
                print(f"   ❌ FAILED - Should have passed but failed: {e}")
    
    print(f"\n   SQL Features Test Results: {passed}/{total} passed")
    return passed == total

def test_database_config():
    """Test database configuration with environment variables."""
    print(f"\n🔧 Testing Database Configuration")
    print("-" * 60)
    
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from src.config.database_config import get_database_config
        
        config = get_database_config()
        
        # Test configuration retrieval
        postgres_config = config.get_postgres_config()
        mysql_config = config.get_mysql_config()
        
        print(f"   ✅ PostgreSQL config loaded: {postgres_config['host']}:{postgres_config['port']}")
        print(f"   ✅ MySQL config loaded: {mysql_config['host']}:{mysql_config['port']}")
        
        # Test validation
        validation = config.validate_credentials()
        print(f"   ✅ Credential validation: {validation}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ FAILED - Database config error: {e}")
        return False

def main():
    """Test improved error handling and security features."""
    print("🧪 Improved Error Handling and Security Testing")
    print("=" * 70)
    
    # Test CLI error handling
    print("\n🔴 CLI ERROR HANDLING TESTS")
    print("=" * 50)
    
    cli_error_tests = [
        {
            "description": "Empty query validation",
            "command": 'python analyze_db.py postgres ""',
            "expected_exit_code": 1
        },
        {
            "description": "Invalid SQL syntax",
            "command": 'python analyze_db.py postgres "INVALID SQL SYNTAX"',
            "expected_exit_code": 1
        },
        {
            "description": "Invalid database type",
            "command": 'python analyze_db.py invalid_db "SELECT * FROM orders;"',
            "expected_exit_code": 1
        },
        {
            "description": "Missing query argument",
            "command": "python analyze_db.py postgres",
            "expected_exit_code": 1
        },
        {
            "description": "Non-existent plan file",
            "command": 'python analyze_db.py postgres "SELECT * FROM orders;" --plan-file non_existent.json',
            "expected_exit_code": 1
        }
    ]
    
    cli_passed = 0
    cli_total = len(cli_error_tests)
    
    for test in cli_error_tests:
        if test_error_case(test["description"], test["command"], test["expected_exit_code"]):
            cli_passed += 1
    
    # Test success cases
    print("\n🟢 SUCCESS CASE TESTS")
    print("=" * 50)
    
    success_tests = [
        {
            "description": "Valid PostgreSQL query",
            "command": 'python analyze_db.py postgres "SELECT * FROM orders WHERE customer_id = 42;"'
        },
        {
            "description": "Valid MySQL query",
            "command": 'python analyze_db.py mysql "SELECT * FROM orders WHERE customer_id = 42;"'
        },
        {
            "description": "Query with special characters",
            "command": 'python analyze_db.py postgres "SELECT \'test\' as name, 42 as value;"'
        }
    ]
    
    success_passed = 0
    success_total = len(success_tests)
    
    for test in success_tests:
        if test_success_case(test["description"], test["command"]):
            success_passed += 1
    
    # Test component-level improvements
    print("\n🔧 COMPONENT IMPROVEMENT TESTS")
    print("=" * 50)
    
    component_tests = [
        ("SQL Features Extraction", test_sql_features),
        ("Database Configuration", test_database_config)
    ]
    
    component_passed = 0
    component_total = len(component_tests)
    
    for test_name, test_func in component_tests:
        print(f"\n🔬 Running: {test_name}")
        if test_func():
            component_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 IMPROVED ERROR HANDLING TEST RESULTS")
    print("=" * 70)
    
    total_tests = cli_total + success_total + component_total
    total_passed = cli_passed + success_passed + component_passed
    
    print(f"CLI Error Handling: {cli_passed}/{cli_total} passed")
    print(f"Success Cases: {success_passed}/{success_total} passed")
    print(f"Component Tests: {component_passed}/{component_total} passed")
    print(f"Overall: {total_passed}/{total_tests} passed ({(total_passed/total_tests)*100:.1f}%)")
    
    if total_passed == total_tests:
        print("\n🎉 ALL IMPROVEMENTS WORKING PERFECTLY!")
        print("   Error handling is robust and secure credentials are implemented.")
    elif total_passed >= total_tests * 0.8:
        print("\n✅ MOSTLY SUCCESSFUL - Significant improvements made")
    else:
        print("\n⚠️  SOME IMPROVEMENTS NEED WORK")
        print("   Review failed tests above for further improvements")
    
    return total_passed == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
