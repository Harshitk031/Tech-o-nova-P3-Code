#!/usr/bin/env python3
"""
Performance Regression Analysis Module
Analyzes historical performance data to detect performance regressions.
"""

import psycopg2
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import statistics

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.database_config import get_database_config

class PerformanceRegressionAnalyzer:
    """Analyzes performance regressions in historical data."""
    
    def __init__(self, historical_db_name: str = "performance_history"):
        """Initialize the regression analyzer."""
        self.historical_db_name = historical_db_name
        self.db_config = get_database_config()
        
        # PostgreSQL connection for historical data
        self.historical_conn_str = self.db_config.get_postgres_connection_string().replace(
            f"/{self.db_config.get_postgres_config()['database']}", 
            f"/{historical_db_name}"
        )
    
    def analyze_query_regression(self, query_id: int, days: int = 7, threshold: float = 0.5) -> Dict[str, Any]:
        """
        Analyze performance regression for a specific query.
        
        Args:
            query_id: The query ID to analyze
            days: Number of days to look back for historical data
            threshold: Performance regression threshold (0.5 = 50% increase)
            
        Returns:
            Dictionary containing regression analysis results
        """
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    # Get historical performance data
                    historical_query = """
                    SELECT 
                        captured_at,
                        total_exec_time_ms,
                        mean_exec_time_ms,
                        calls
                    FROM query_snapshots
                    WHERE query_id = %s
                    AND captured_at >= NOW() - INTERVAL '%s days'
                    ORDER BY captured_at ASC
                    """
                    
                    cur.execute(historical_query, (query_id, days))
                    historical_data = cur.fetchall()
                    
                    if len(historical_data) < 2:
                        return {
                            'query_id': query_id,
                            'status': 'insufficient_data',
                            'message': f'Insufficient data for regression analysis (need at least 2 data points, got {len(historical_data)})',
                            'data_points': len(historical_data)
                        }
                    
                    # Get query details
                    query_details_query = """
                    SELECT query_text, database_name
                    FROM query_snapshots
                    WHERE query_id = %s
                    LIMIT 1
                    """
                    
                    cur.execute(query_details_query, (query_id,))
                    query_details = cur.fetchone()
                    
                    if not query_details:
                        return {
                            'query_id': query_id,
                            'status': 'query_not_found',
                            'message': 'Query not found in historical data'
                        }
                    
                    query_text, database_name = query_details
                    
                    # Analyze performance trends
                    execution_times = [row[1] for row in historical_data]  # total_exec_time_ms
                    mean_times = [row[2] for row in historical_data]  # mean_exec_time_ms
                    call_counts = [row[3] for row in historical_data]  # calls
                    
                    # Calculate statistics
                    historical_avg = statistics.mean(execution_times)
                    historical_median = statistics.median(execution_times)
                    historical_std = statistics.stdev(execution_times) if len(execution_times) > 1 else 0
                    
                    # Get most recent performance
                    recent_time = execution_times[-1]
                    recent_mean = mean_times[-1]
                    recent_calls = call_counts[-1]
                    
                    # Calculate regression metrics
                    regression_percentage = ((recent_time - historical_avg) / historical_avg) * 100
                    is_regression = regression_percentage > (threshold * 100)
                    
                    # Calculate trend direction
                    if len(execution_times) >= 3:
                        # Use linear regression slope for trend
                        x = list(range(len(execution_times)))
                        slope = self._calculate_slope(x, execution_times)
                        trend_direction = 'improving' if slope < 0 else 'degrading' if slope > 0 else 'stable'
                    else:
                        trend_direction = 'insufficient_data'
                    
                    # Calculate confidence score
                    confidence = self._calculate_confidence(len(historical_data), historical_std, recent_calls)
                    
                    # Determine severity
                    severity = self._determine_severity(regression_percentage, confidence)
                    
                    return {
                        'query_id': query_id,
                        'database_name': database_name,
                        'query_text': query_text[:200] + '...' if len(query_text) > 200 else query_text,
                        'status': 'analyzed',
                        'is_regression': is_regression,
                        'regression_percentage': round(regression_percentage, 2),
                        'severity': severity,
                        'confidence': round(confidence, 2),
                        'trend_direction': trend_direction,
                        'historical_stats': {
                            'avg_exec_time_ms': round(historical_avg, 2),
                            'median_exec_time_ms': round(historical_median, 2),
                            'std_deviation_ms': round(historical_std, 2),
                            'data_points': len(historical_data)
                        },
                        'recent_performance': {
                            'exec_time_ms': round(recent_time, 2),
                            'mean_exec_time_ms': round(recent_mean, 2),
                            'calls': recent_calls
                        },
                        'analysis_period_days': days,
                        'threshold_percentage': threshold * 100,
                        'analyzed_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            return {
                'query_id': query_id,
                'status': 'error',
                'message': f'Error analyzing regression: {str(e)}'
            }
    
    def find_all_regressions(self, days: int = 7, threshold: float = 0.5, min_calls: int = 10) -> List[Dict[str, Any]]:
        """
        Find all queries with performance regressions.
        
        Args:
            days: Number of days to look back
            threshold: Performance regression threshold
            min_calls: Minimum number of calls for analysis
            
        Returns:
            List of regression analysis results
        """
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    # Get all query IDs with sufficient data
                    query_ids_query = """
                    SELECT DISTINCT query_id
                    FROM query_snapshots
                    WHERE captured_at >= NOW() - INTERVAL '%s days'
                    AND calls >= %s
                    ORDER BY query_id
                    """
                    
                    cur.execute(query_ids_query, (days, min_calls))
                    query_ids = [row[0] for row in cur.fetchall()]
                    
                    regressions = []
                    for query_id in query_ids:
                        analysis = self.analyze_query_regression(query_id, days, threshold)
                        if analysis.get('is_regression', False):
                            regressions.append(analysis)
                    
                    # Sort by regression percentage (worst first)
                    regressions.sort(key=lambda x: x.get('regression_percentage', 0), reverse=True)
                    
                    return regressions
                    
        except Exception as e:
            print(f"Error finding regressions: {e}")
            return []
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get overall performance summary with regression insights."""
        try:
            with psycopg2.connect(self.historical_conn_str) as conn:
                with conn.cursor() as cur:
                    # Get summary statistics
                    summary_query = """
                    SELECT 
                        COUNT(DISTINCT query_id) as total_queries,
                        COUNT(*) as total_snapshots,
                        AVG(total_exec_time_ms) as avg_exec_time,
                        MAX(total_exec_time_ms) as max_exec_time,
                        MIN(total_exec_time_ms) as min_exec_time,
                        SUM(calls) as total_calls
                    FROM query_snapshots
                    WHERE captured_at >= NOW() - INTERVAL '%s days'
                    """
                    
                    cur.execute(summary_query, (days,))
                    summary = dict(zip([desc[0] for desc in cur.description], cur.fetchone()))
                    
                    # Get regression count
                    regressions = self.find_all_regressions(days, 0.3)  # Lower threshold for summary
                    regression_count = len(regressions)
                    
                    # Get worst performers
                    worst_queries_query = """
                    SELECT 
                        query_id,
                        query_text,
                        AVG(total_exec_time_ms) as avg_exec_time,
                        SUM(calls) as total_calls
                    FROM query_snapshots
                    WHERE captured_at >= NOW() - INTERVAL '%s days'
                    GROUP BY query_id, query_text
                    ORDER BY avg_exec_time DESC
                    LIMIT 5
                    """
                    
                    cur.execute(worst_queries_query, (days,))
                    worst_queries = []
                    for row in cur.fetchall():
                        worst_queries.append({
                            'query_id': row[0],
                            'query_text': row[1][:100] + '...' if len(row[1]) > 100 else row[1],
                            'avg_exec_time_ms': round(row[2], 2),
                            'total_calls': row[3]
                        })
                    
                    return {
                        'summary': summary,
                        'regression_count': regression_count,
                        'worst_queries': worst_queries,
                        'analysis_period_days': days,
                        'generated_at': datetime.now().isoformat()
                    }
                    
        except Exception as e:
            print(f"Error getting performance summary: {e}")
            return {}
    
    def _calculate_slope(self, x: List[float], y: List[float]) -> float:
        """Calculate linear regression slope."""
        n = len(x)
        if n < 2:
            return 0
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope
    
    def _calculate_confidence(self, data_points: int, std_dev: float, recent_calls: int) -> float:
        """Calculate confidence score for regression analysis."""
        # Base confidence on data points and call volume
        data_confidence = min(data_points / 10, 1.0)  # More data points = higher confidence
        call_confidence = min(recent_calls / 100, 1.0)  # More calls = higher confidence
        
        # Lower std deviation = higher confidence (more consistent data)
        consistency_confidence = max(0, 1 - (std_dev / 1000))  # Normalize std dev
        
        # Weighted average
        confidence = (data_confidence * 0.4 + call_confidence * 0.4 + consistency_confidence * 0.2)
        return min(confidence, 1.0)
    
    def _determine_severity(self, regression_percentage: float, confidence: float) -> str:
        """Determine regression severity based on percentage and confidence."""
        if regression_percentage > 200 and confidence > 0.7:
            return 'CRITICAL'
        elif regression_percentage > 100 and confidence > 0.5:
            return 'HIGH'
        elif regression_percentage > 50 and confidence > 0.3:
            return 'MEDIUM'
        elif regression_percentage > 20:
            return 'LOW'
        else:
            return 'MINIMAL'

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze performance regressions")
    parser.add_argument('--query-id', type=int, help='Specific query ID to analyze')
    parser.add_argument('--days', type=int, default=7, help='Days to look back')
    parser.add_argument('--threshold', type=float, default=0.5, help='Regression threshold (0.5 = 50 percent)')
    parser.add_argument('--min-calls', type=int, default=10, help='Minimum calls for analysis')
    parser.add_argument('--output', help='Output file for JSON results')
    parser.add_argument('--historical-db', default='performance_history', help='Historical database name')
    
    args = parser.parse_args()
    
    analyzer = PerformanceRegressionAnalyzer(args.historical_db)
    
    try:
        if args.query_id:
            # Analyze specific query
            result = analyzer.analyze_query_regression(args.query_id, args.days, args.threshold)
            print(json.dumps(result, indent=2))
        else:
            # Find all regressions
            regressions = analyzer.find_all_regressions(args.days, args.threshold, args.min_calls)
            summary = analyzer.get_performance_summary(args.days)
            
            if args.output:
                data = {
                    'regressions': regressions,
                    'summary': summary
                }
                with open(args.output, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"Results saved to: {args.output}")
            else:
                print(f"Found {len(regressions)} performance regressions")
                for reg in regressions[:5]:  # Show top 5
                    print(f"- Query {reg['query_id']}: {reg['regression_percentage']:.1f}% regression ({reg['severity']})")
                
    except KeyboardInterrupt:
        print("\n⏹️  Analysis cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    import json
    main()