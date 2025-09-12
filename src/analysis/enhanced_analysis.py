#!/usr/bin/env python3
"""
Enhanced Analysis Pipeline
Integrates regression analysis, configuration analysis, and schema analysis.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.analysis.regression_analysis import PerformanceRegressionAnalyzer
from src.analysis.configuration_analysis import ConfigurationAnalyzer
from src.analysis.schema_analysis import SchemaAnalyzer
from src.analysis.comprehensive_analysis import (
    analyze_postgres_query_with_unused_indexes,
    analyze_mysql_query_with_unused_indexes
)

class EnhancedAnalysisPipeline:
    """Enhanced analysis pipeline with advanced features."""
    
    def __init__(self, historical_db_name: str = "performance_history"):
        """Initialize the enhanced analysis pipeline."""
        self.regression_analyzer = PerformanceRegressionAnalyzer(historical_db_name)
        self.config_analyzer = ConfigurationAnalyzer()
        self.schema_analyzer = SchemaAnalyzer()
    
    def analyze_query_with_regression(self, sql_query: str, database_type: str = 'postgresql') -> Dict[str, Any]:
        """Analyze a query with regression analysis."""
        # Get basic analysis
        if database_type == 'postgresql':
            basic_analysis = analyze_postgres_query_with_unused_indexes(sql_query)
        else:
            basic_analysis = analyze_mysql_query_with_unused_indexes(sql_query)
        
        # Add regression analysis if we have historical data
        regression_analysis = None
        try:
            # Try to find the query in historical data
            regressions = self.regression_analyzer.find_all_regressions(days=7, threshold=0.3)
            for reg in regressions:
                if sql_query.strip() in reg.get('query_text', ''):
                    regression_analysis = reg
                    break
        except Exception as e:
            regression_analysis = {'error': f'Regression analysis failed: {str(e)}'}
        
        # Combine results
        enhanced_analysis = {
            'query': sql_query,
            'database_type': database_type,
            'basic_analysis': basic_analysis,
            'regression_analysis': regression_analysis,
            'analyzed_at': datetime.now().isoformat()
        }
        
        return enhanced_analysis
    
    def analyze_database_health(self, database_type: str = 'both') -> Dict[str, Any]:
        """Perform comprehensive database health analysis."""
        health_analysis = {
            'analysis_type': 'database_health',
            'analyzed_at': datetime.now().isoformat(),
            'components': {}
        }
        
        # Configuration analysis
        if database_type in ['postgresql', 'both']:
            print("🔍 Analyzing PostgreSQL configuration...")
            health_analysis['components']['postgresql_config'] = self.config_analyzer.analyze_postgresql_configuration()
        
        if database_type in ['mysql', 'both']:
            print("🔍 Analyzing MySQL configuration...")
            health_analysis['components']['mysql_config'] = self.config_analyzer.analyze_mysql_configuration()
        
        # Schema analysis
        if database_type in ['postgresql', 'both']:
            print("🔍 Analyzing PostgreSQL schema...")
            health_analysis['components']['postgresql_schema'] = self.schema_analyzer.analyze_postgresql_schema()
        
        if database_type in ['mysql', 'both']:
            print("🔍 Analyzing MySQL schema...")
            health_analysis['components']['mysql_schema'] = self.schema_analyzer.analyze_mysql_schema()
        
        # Performance regression analysis
        print("🔍 Analyzing performance regressions...")
        try:
            regressions = self.regression_analyzer.find_all_regressions(days=7, threshold=0.5)
            health_analysis['components']['performance_regressions'] = {
                'regression_count': len(regressions),
                'regressions': regressions[:10],  # Top 10 regressions
                'summary': self.regression_analyzer.get_performance_summary(days=7)
            }
        except Exception as e:
            health_analysis['components']['performance_regressions'] = {
                'error': f'Regression analysis failed: {str(e)}'
            }
        
        return health_analysis
    
    def generate_enhanced_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate an enhanced analysis report."""
        report = []
        report.append("=" * 80)
        report.append("🧠 ENHANCED DATABASE PERFORMANCE ANALYSIS")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Basic analysis results
        if 'basic_analysis' in analysis_results:
            basic = analysis_results['basic_analysis']
            report.append("📊 BASIC ANALYSIS RESULTS")
            report.append("-" * 40)
            report.append(f"Query: {analysis_results.get('query', 'N/A')}")
            report.append(f"Database: {analysis_results.get('database_type', 'N/A')}")
            
            recommendations = basic.get('recommendations', [])
            report.append(f"Recommendations: {len(recommendations)}")
            
            for i, rec in enumerate(recommendations[:3], 1):
                report.append(f"  {i}. {rec.get('type', 'Unknown')} - {rec.get('severity', 'Unknown')} severity")
                report.append(f"     {rec.get('suggested_action', 'No action')[:60]}...")
            report.append("")
        
        # Regression analysis results
        if 'regression_analysis' in analysis_results:
            regression = analysis_results['regression_analysis']
            if regression and 'error' not in regression:
                report.append("📈 REGRESSION ANALYSIS")
                report.append("-" * 40)
                if regression.get('is_regression', False):
                    report.append(f"⚠️  PERFORMANCE REGRESSION DETECTED")
                    report.append(f"   Regression: {regression.get('regression_percentage', 0):.1f}%")
                    report.append(f"   Severity: {regression.get('severity', 'Unknown')}")
                    report.append(f"   Confidence: {regression.get('confidence', 0):.2f}")
                else:
                    report.append("✅ No significant performance regression detected")
                report.append("")
        
        # Database health results
        if 'components' in analysis_results:
            components = analysis_results['components']
            
            # Configuration analysis
            for db_type in ['postgresql', 'mysql']:
                config_key = f'{db_type}_config'
                if config_key in components:
                    config = components[config_key]
                    if 'recommendations' in config:
                        recs = config['recommendations']
                        if recs:
                            report.append(f"⚙️  {db_type.upper()} CONFIGURATION ISSUES")
                            report.append("-" * 40)
                            for rec in recs[:3]:
                                report.append(f"  • {rec.get('setting', 'Unknown')}: {rec.get('issue', 'Unknown')}")
                                report.append(f"    {rec.get('recommendation', 'No recommendation')[:60]}...")
                            report.append("")
            
            # Schema analysis
            for db_type in ['postgresql', 'mysql']:
                schema_key = f'{db_type}_schema'
                if schema_key in components:
                    schema = components[schema_key]
                    if 'recommendations' in schema:
                        recs = schema['recommendations']
                        if recs:
                            report.append(f"🏗️  {db_type.upper()} SCHEMA ISSUES")
                            report.append("-" * 40)
                            for rec in recs[:3]:
                                report.append(f"  • {rec.get('table', 'Unknown')}.{rec.get('column', 'Unknown')}: {rec.get('issue', 'Unknown')}")
                                report.append(f"    {rec.get('recommendation', 'No recommendation')[:60]}...")
                            report.append("")
            
            # Performance regressions
            if 'performance_regressions' in components:
                regressions = components['performance_regressions']
                if 'regression_count' in regressions:
                    count = regressions['regression_count']
                    report.append(f"📉 PERFORMANCE REGRESSIONS")
                    report.append("-" * 40)
                    report.append(f"Total regressions found: {count}")
                    
                    if count > 0 and 'regressions' in regressions:
                        for reg in regressions['regressions'][:3]:
                            report.append(f"  • Query {reg.get('query_id', 'Unknown')}: {reg.get('regression_percentage', 0):.1f}% regression")
                    report.append("")
        
        return "\n".join(report)

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced database analysis pipeline")
    parser.add_argument('--query', help='SQL query to analyze')
    parser.add_argument('--database', choices=['postgresql', 'mysql', 'both'], default='both', help='Database type')
    parser.add_argument('--health-check', action='store_true', help='Perform database health check')
    parser.add_argument('--output', help='Output file for JSON results')
    parser.add_argument('--report', action='store_true', help='Generate text report')
    parser.add_argument('--historical-db', default='performance_history', help='Historical database name')
    
    args = parser.parse_args()
    
    pipeline = EnhancedAnalysisPipeline(args.historical_db)
    
    try:
        if args.query:
            # Analyze specific query
            print(f"Analyzing query: {args.query}")
            results = pipeline.analyze_query_with_regression(args.query, args.database)
        elif args.health_check:
            # Perform health check
            print("Performing database health check...")
            results = pipeline.analyze_database_health(args.database)
        else:
            print("Please specify --query or --health-check")
            sys.exit(1)
        
        if args.report:
            report = pipeline.generate_enhanced_report(results)
            print(report)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to: {args.output}")
        elif not args.report:
            print(json.dumps(results, indent=2))
            
    except KeyboardInterrupt:
        print("\nAnalysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()