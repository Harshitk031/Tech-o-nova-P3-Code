#!/usr/bin/env python3
"""
Test script for error handling and edge cases
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

def main():
    """Test error handling and edge cases."""
    print("🧪 Error Handling and Edge Cases Testing")
    print("=" * 70)
    
    # Error cases
    error_tests = [
        {
            "description": "Invalid SQL syntax",
            "command": 'python analyze_db.py postgres "INVALID SQL SYNTAX HERE;"',
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
            "description": "Invalid format option",
            "command": 'python analyze_db.py postgres "SELECT * FROM orders;" --format invalid',
            "expected_exit_code": 1
        },
        {
            "description": "Non-existent plan file",
            "command": 'python analyze_db.py postgres "SELECT * FROM orders;" --plan-file non_existent.json',
            "expected_exit_code": 1
        }
    ]
    
    # Success cases (edge cases that should work)
    success_tests = [
        {
            "description": "Empty query (should be handled gracefully)",
            "command": 'python analyze_db.py postgres ""'
        },
        {
            "description": "Query with special characters",
            "command": 'python analyze_db.py postgres "SELECT \'test\' as name, 42 as value;"'
        },
        {
            "description": "Very long query",
            "command": 'python analyze_db.py postgres "SELECT * FROM orders WHERE customer_id = 42 AND amount > 100 AND created_at > \'2023-01-01\' ORDER BY created_at DESC LIMIT 10;"'
        },
        {
            "description": "Query with comments",
            "command": 'python analyze_db.py postgres "-- This is a comment\nSELECT * FROM orders WHERE customer_id = 42; -- Another comment"'
        }
    ]
    
    # Run error tests
    print("\n🔴 ERROR HANDLING TESTS")
    print("=" * 50)
    
    error_passed = 0
    error_total = len(error_tests)
    
    for test in error_tests:
        if test_error_case(test["description"], test["command"], test["expected_exit_code"]):
            error_passed += 1
    
    # Run success tests
    print("\n🟢 EDGE CASE SUCCESS TESTS")
    print("=" * 50)
    
    success_passed = 0
    success_total = len(success_tests)
    
    for test in success_tests:
        if test_success_case(test["description"], test["command"]):
            success_passed += 1
    
    # Test component-level error handling
    print("\n🔧 COMPONENT ERROR HANDLING TESTS")
    print("=" * 50)
    
    component_tests = [
        {
            "description": "SQL features with invalid query",
            "command": "python -c \"from src.analysis.sql_features import extract_sql_features; extract_sql_features('INVALID SQL')\""
        },
        {
            "description": "Plan parser with non-existent file",
            "command": "python -c \"from src.parsers.postgres_plan import parse_postgres_plan; parse_postgres_plan('non_existent.json')\""
        }
    ]
    
    component_passed = 0
    component_total = len(component_tests)
    
    for test in component_tests:
        if test_error_case(test["description"], test["command"], 1):
            component_passed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 ERROR HANDLING TEST RESULTS")
    print("=" * 70)
    
    total_tests = error_total + success_total + component_total
    total_passed = error_passed + success_passed + component_passed
    
    print(f"Error Handling Tests: {error_passed}/{error_total} passed")
    print(f"Edge Case Success Tests: {success_passed}/{success_total} passed")
    print(f"Component Error Tests: {component_passed}/{component_total} passed")
    print(f"Overall: {total_passed}/{total_tests} passed ({(total_passed/total_tests)*100:.1f}%)")
    
    if total_passed == total_tests:
        print("\n🎉 ALL ERROR HANDLING TESTS PASSED!")
        print("   The system handles errors gracefully and robustly.")
    elif total_passed >= total_tests * 0.8:
        print("\n✅ MOSTLY SUCCESSFUL - Good error handling with minor issues")
    else:
        print("\n⚠️  SOME ERROR HANDLING ISSUES DETECTED")
        print("   Review failed tests above for improvement areas")
    
    return total_passed == total_tests

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
