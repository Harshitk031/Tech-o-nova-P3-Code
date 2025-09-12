#!/usr/bin/env python3
"""
Test script for multiple query types and end-to-end workflow
"""

import subprocess
import json
import os

def run_analysis(query, db_type, description):
    """Run analysis for a specific query and return results."""
    print(f"\n🔍 Testing: {description}")
    print(f"   Query: {query}")
    print(f"   Database: {db_type}")
    print("-" * 60)
    
    try:
        # Run the analysis
        cmd = f'python analyze_db.py {db_type} "{query}" --format json'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        
        # Parse JSON output
        output_lines = result.stdout.strip().split('\n')
        json_start = -1
        for i, line in enumerate(output_lines):
            if line.strip().startswith('{'):
                json_start = i
                break
        
        if json_start >= 0:
            json_output = '\n'.join(output_lines[json_start:])
            data = json.loads(json_output)
            
            recommendations = data.get('recommendations', [])
            print(f"   ✅ Analysis completed")
            print(f"   📊 Recommendations: {len(recommendations)}")
            
            if recommendations:
                for i, rec in enumerate(recommendations[:2]):  # Show first 2
                    print(f"      {i+1}. {rec.get('type', 'Unknown')} - {rec.get('severity', 'Unknown')} severity")
                    print(f"         Action: {rec.get('suggested_action', 'No action')[:50]}...")
            
            return True, data
        else:
            print(f"   ❌ No JSON output found")
            return False, None
            
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Analysis failed: {e}")
        print(f"   Error output: {e.stderr}")
        return False, None
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON parsing failed: {e}")
        return False, None
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False, None

def main():
    """Test multiple query types and workflows."""
    print("🧪 End-to-End Workflow Testing with Multiple Queries")
    print("=" * 70)
    
    # Test queries covering different scenarios
    test_cases = [
        # PostgreSQL tests
        {
            "query": "SELECT * FROM orders WHERE customer_id = 42;",
            "db_type": "postgres",
            "description": "Basic WHERE clause (should find missing index)"
        },
        {
            "query": "SELECT * FROM orders WHERE amount > 1000 ORDER BY created_at DESC;",
            "db_type": "postgres", 
            "description": "WHERE + ORDER BY (should find missing index + sort issue)"
        },
        {
            "query": "SELECT COUNT(*) FROM orders;",
            "db_type": "postgres",
            "description": "Aggregate query (should be efficient)"
        },
        {
            "query": "SELECT * FROM orders WHERE id = 1;",
            "db_type": "postgres",
            "description": "Primary key lookup (should use index)"
        },
        
        # MySQL tests
        {
            "query": "SELECT * FROM orders WHERE customer_id = 42;",
            "db_type": "mysql",
            "description": "Basic WHERE clause (MySQL)"
        },
        {
            "query": "SELECT * FROM orders WHERE amount > 1000 ORDER BY created_at DESC;",
            "db_type": "mysql",
            "description": "WHERE + ORDER BY (MySQL)"
        },
        {
            "query": "SELECT COUNT(*) FROM orders;",
            "db_type": "mysql",
            "description": "Aggregate query (MySQL)"
        }
    ]
    
    results = []
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}/{total}")
        success, data = run_analysis(
            test_case["query"],
            test_case["db_type"], 
            test_case["description"]
        )
        
        results.append({
            "test_case": i,
            "description": test_case["description"],
            "query": test_case["query"],
            "database": test_case["db_type"],
            "success": success,
            "recommendations_count": len(data.get('recommendations', [])) if data else 0
        })
        
        if success:
            passed += 1
            print(f"   ✅ PASSED")
        else:
            print(f"   ❌ FAILED")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 END-TO-END WORKFLOW TEST RESULTS")
    print("=" * 70)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"   {result['test_case']:2d}. {status} - {result['description']}")
        print(f"       Database: {result['database']}, Recommendations: {result['recommendations_count']}")
    
    # Test comprehensive analysis
    print(f"\n🔬 TESTING COMPREHENSIVE ANALYSIS (BOTH DATABASES)")
    print("-" * 70)
    
    try:
        cmd = 'python analyze_db.py both "SELECT * FROM orders WHERE customer_id = 42;" --format json'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print("✅ Comprehensive analysis (both databases) completed successfully")
    except Exception as e:
        print(f"❌ Comprehensive analysis failed: {e}")
    
    # Test validation harness
    print(f"\n🔧 TESTING VALIDATION HARNESS")
    print("-" * 70)
    
    try:
        cmd = 'python scripts/validate_recommendation.py'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print("✅ Validation harness completed successfully")
    except Exception as e:
        print(f"❌ Validation harness failed: {e}")
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if passed == total:
        print("🎉 ALL TESTS PASSED - System is working perfectly!")
    elif passed >= total * 0.8:
        print("✅ MOSTLY SUCCESSFUL - System is working well with minor issues")
    else:
        print("⚠️  SOME ISSUES DETECTED - Check failed tests above")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
