#!/usr/bin/env python3
"""
Test script for comprehensive analysis pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.analysis.comprehensive_analysis import (
    analyze_postgres_query_with_unused_indexes,
    analyze_mysql_query_with_unused_indexes,
    format_comprehensive_report
)

def test_postgres_analysis():
    """Test PostgreSQL comprehensive analysis."""
    print("🔍 Testing PostgreSQL Comprehensive Analysis")
    print("=" * 50)
    
    try:
        result = analyze_postgres_query_with_unused_indexes('SELECT * FROM orders WHERE customer_id = 42;')
        
        print(f"✅ Analysis completed successfully")
        print(f"   Recommendations: {len(result.get('recommendations', []))}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"   Impact: {result.get('impact', 'N/A')}")
        
        # Show first recommendation if any
        recommendations = result.get('recommendations', [])
        if recommendations:
            first_rec = recommendations[0]
            print(f"   First Recommendation: {first_rec.get('type', 'Unknown')}")
            print(f"   Action: {first_rec.get('suggested_action', 'No action')[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ PostgreSQL analysis failed: {e}")
        return False

def test_mysql_analysis():
    """Test MySQL comprehensive analysis."""
    print("\n🔍 Testing MySQL Comprehensive Analysis")
    print("=" * 50)
    
    try:
        result = analyze_mysql_query_with_unused_indexes('SELECT * FROM orders WHERE customer_id = 42;')
        
        print(f"✅ Analysis completed successfully")
        print(f"   Recommendations: {len(result.get('recommendations', []))}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"   Impact: {result.get('impact', 'N/A')}")
        
        # Show first recommendation if any
        recommendations = result.get('recommendations', [])
        if recommendations:
            first_rec = recommendations[0]
            print(f"   First Recommendation: {first_rec.get('type', 'Unknown')}")
            print(f"   Action: {first_rec.get('suggested_action', 'No action')[:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ MySQL analysis failed: {e}")
        return False

def test_report_formatting():
    """Test report formatting."""
    print("\n📄 Testing Report Formatting")
    print("=" * 50)
    
    try:
        # Create sample data
        sample_data = {
            'postgresql': {
                'recommendations': [{
                    'type': 'MISSING_INDEX',
                    'suggested_action': 'CREATE INDEX idx_orders_customer_id ON orders (customer_id);',
                    'confidence': 0.95,
                    'impact': 'High'
                }],
                'confidence': 0.95,
                'impact': 'High'
            }
        }
        
        report = format_comprehensive_report(sample_data)
        print(f"✅ Report formatting successful")
        print(f"   Report length: {len(report)} characters")
        print(f"   Contains recommendations: {'MISSING_INDEX' in report}")
        
        return True
    except Exception as e:
        print(f"❌ Report formatting failed: {e}")
        return False

def main():
    """Run all comprehensive analysis tests."""
    print("🧪 Comprehensive Analysis Pipeline Testing")
    print("=" * 60)
    
    tests = [
        ("PostgreSQL Analysis", test_postgres_analysis),
        ("MySQL Analysis", test_mysql_analysis),
        ("Report Formatting", test_report_formatting)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        if test_func():
            passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All comprehensive analysis tests PASSED!")
    else:
        print("⚠️  Some tests failed - check the output above")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
