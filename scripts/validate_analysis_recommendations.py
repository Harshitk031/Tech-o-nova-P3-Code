#!/usr/bin/env python3
"""
Validate Analysis Recommendations
Validates recommendations from the comprehensive analysis pipeline.
"""

import json
import sys
import os
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util
spec = importlib.util.spec_from_file_location("validate_recommendation", "scripts/validate_recommendation.py")
validate_recommendation_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_recommendation_module)
ValidationHarness = validate_recommendation_module.ValidationHarness

def load_analysis_results(file_path: str) -> Dict[str, Any]:
    """Load analysis results from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading analysis results: {e}")
        return {}

def validate_recommendations_from_analysis(analysis_file: str, database_type: str = 'postgresql') -> List[Dict[str, Any]]:
    """
    Validate recommendations from a comprehensive analysis file.
    
    Args:
        analysis_file: Path to analysis results JSON file
        database_type: Database type to validate against
        
    Returns:
        List of validation results
    """
    print(f"🔍 Loading analysis results from: {analysis_file}")
    analysis_results = load_analysis_results(analysis_file)
    
    if not analysis_results:
        print("❌ No analysis results found")
        return []
    
    # Extract recommendations
    recommendations = []
    if 'postgresql' in analysis_results:
        recommendations.extend(analysis_results['postgresql'].get('recommendations', []))
    if 'mysql' in analysis_results:
        recommendations.extend(analysis_results['mysql'].get('recommendations', []))
    
    if not recommendations:
        print("❌ No recommendations found in analysis results")
        return []
    
    print(f"📋 Found {len(recommendations)} recommendations to validate")
    
    # Filter recommendations by type and database
    index_recommendations = [
        rec for rec in recommendations 
        if rec.get('type') in ['MISSING_INDEX', 'UNUSED_INDEX_CANDIDATE'] 
        and 'suggested_action' in rec
    ]
    
    if not index_recommendations:
        print("❌ No index recommendations found to validate")
        return []
    
    print(f"🎯 Found {len(index_recommendations)} index recommendations to validate")
    
    # Validate each recommendation
    validation_results = []
    harness = ValidationHarness(database_type)
    
    for i, recommendation in enumerate(index_recommendations, 1):
        print(f"\n{'='*60}")
        print(f"🧪 Validating Recommendation {i}/{len(index_recommendations)}")
        print(f"{'='*60}")
        print(f"Type: {recommendation.get('type', 'UNKNOWN')}")
        print(f"Severity: {recommendation.get('severity', 'UNKNOWN')}")
        print(f"Rationale: {recommendation.get('rationale', 'N/A')}")
        print(f"Action: {recommendation.get('suggested_action', 'N/A')}")
        
        # Extract query from analysis results
        query = None
        if 'postgresql' in analysis_results:
            query = analysis_results['postgresql'].get('query')
        elif 'mysql' in analysis_results:
            query = analysis_results['mysql'].get('query')
        
        if not query:
            print("❌ No query found in analysis results")
            continue
        
        # Validate the recommendation
        result = harness.validate_recommendation(
            query,
            recommendation['suggested_action'],
            iterations=3
        )
        
        # Add recommendation metadata to result
        result['recommendation_metadata'] = {
            'type': recommendation.get('type'),
            'severity': recommendation.get('severity'),
            'rule_id': recommendation.get('rule_id'),
            'rationale': recommendation.get('rationale'),
            'confidence': recommendation.get('confidence'),
            'impact': recommendation.get('impact')
        }
        
        validation_results.append(result)
    
    return validation_results

def generate_validation_report(validation_results: List[Dict[str, Any]]) -> str:
    """Generate a comprehensive validation report."""
    if not validation_results:
        return "❌ No validation results to report"
    
    report = []
    report.append("=" * 80)
    report.append("VALIDATION REPORT")
    report.append("=" * 80)
    report.append(f"Total Recommendations Validated: {len(validation_results)}")
    report.append("")
    
    # Summary statistics
    successful = sum(1 for r in validation_results if r.get('success', False))
    excellent = sum(1 for r in validation_results if r.get('improvement', {}).get('overall_improvement') == 'EXCELLENT')
    good = sum(1 for r in validation_results if r.get('improvement', {}).get('overall_improvement') == 'GOOD')
    moderate = sum(1 for r in validation_results if r.get('improvement', {}).get('overall_improvement') == 'MODERATE')
    negative = sum(1 for r in validation_results if r.get('improvement', {}).get('overall_improvement') == 'NEGATIVE')
    
    report.append("SUMMARY STATISTICS:")
    report.append(f"  Successful Validations: {successful}/{len(validation_results)}")
    report.append(f"  Excellent Improvements: {excellent}")
    report.append(f"  Good Improvements: {good}")
    report.append(f"  Moderate Improvements: {moderate}")
    report.append(f"  Negative Results: {negative}")
    report.append("")
    
    # Detailed results
    report.append("DETAILED RESULTS:")
    report.append("")
    
    for i, result in enumerate(validation_results, 1):
        report.append(f"Recommendation #{i}:")
        report.append(f"  Type: {result.get('recommendation_metadata', {}).get('type', 'UNKNOWN')}")
        report.append(f"  Severity: {result.get('recommendation_metadata', {}).get('severity', 'UNKNOWN')}")
        report.append(f"  Rule ID: {result.get('recommendation_metadata', {}).get('rule_id', 'UNKNOWN')}")
        report.append(f"  Success: {'✅' if result.get('success') else '❌'}")
        
        if result.get('success'):
            improvement = result.get('improvement', {})
            report.append(f"  Overall Assessment: {improvement.get('overall_improvement', 'UNKNOWN')}")
            report.append(f"  Time Improvement: {improvement.get('execution_time_percent_improvement', 0):.1f}%")
            report.append(f"  Plan Change: {improvement.get('plan_change', 'N/A')}")
            
            # Recommendation
            overall = improvement.get('overall_improvement', '')
            if overall in ['EXCELLENT', 'GOOD', 'MODERATE']:
                report.append(f"  Recommendation: ✅ KEEP")
            else:
                report.append(f"  Recommendation: ❌ REJECT")
        else:
            report.append(f"  Error: {result.get('error', 'Unknown error')}")
        
        report.append("")
    
    return "\n".join(report)

def main():
    """Main function."""
    print("🔧 Recommendation Validation Tool")
    print("=" * 50)
    
    # Check for analysis file
    analysis_file = "artifacts/comprehensive_analysis.json"
    if not os.path.exists(analysis_file):
        print(f"❌ Analysis file not found: {analysis_file}")
        print("Run the comprehensive analysis first:")
        print("  python src/analysis/comprehensive_analysis.py")
        return
    
    # Validate recommendations
    validation_results = validate_recommendations_from_analysis(analysis_file, 'postgresql')
    
    if not validation_results:
        print("❌ No validation results generated")
        return
    
    # Generate report
    report = generate_validation_report(validation_results)
    print("\n" + report)
    
    # Save results
    output_file = "artifacts/validation_report.json"
    with open(output_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    print(f"\n💾 Validation results saved to: {output_file}")
    
    # Save text report
    report_file = "artifacts/validation_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📄 Text report saved to: {report_file}")

if __name__ == '__main__':
    main()
