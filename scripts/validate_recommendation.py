# scripts/validate_recommendation.py
"""
Validation Harness for Database Performance Recommendations
Tests recommendations by applying them, measuring performance, and cleaning up.
"""

import psycopg2
import mysql.connector
import json
import time
import re
import sys
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.database_config import get_database_config

# Get database configuration
db_config = get_database_config()
POSTGRES_CONN_STR = db_config.get_postgres_connection_string()
MYSQL_CONFIG = db_config.get_mysql_config()

class ValidationHarness:
    """Validates database performance recommendations by testing them in a controlled environment."""
    
    def __init__(self, database_type: str = 'postgresql'):
        """
        Initialize the validation harness.
        
        Args:
            database_type: 'postgresql' or 'mysql'
        """
        self.database_type = database_type.lower()
        self.connection = None
        self.applied_changes = []  # Track changes for cleanup
        
    def connect(self):
        """Establish database connection."""
        try:
            if self.database_type == 'postgresql':
                self.connection = psycopg2.connect(POSTGRES_CONN_STR)
                self.connection.autocommit = True
            elif self.database_type == 'mysql':
                self.connection = mysql.connector.connect(**MYSQL_CONFIG)
            else:
                raise ValueError(f"Unsupported database type: {self.database_type}")
            print(f"✅ Connected to {self.database_type.upper()}")
        except Exception as e:
            print(f"❌ Failed to connect to {self.database_type.upper()}: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print(f"✅ Disconnected from {self.database_type.upper()}")
    
    def get_performance_metrics(self, cursor, query: str) -> Dict[str, Any]:
        """
        Runs EXPLAIN ANALYZE and returns key performance metrics.
        
        Args:
            cursor: Database cursor
            query: SQL query to analyze
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            if self.database_type == 'postgresql':
                cursor.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {query}")
                result = cursor.fetchone()[0][0]
                plan = result['Plan']
                execution_time = result['Execution Time']
                
                return {
                    "node_type": plan['Node Type'],
                    "total_cost": plan['Total Cost'],
                    "execution_time_ms": execution_time,
                    "plan_rows": plan.get('Plan Rows', 0),
                    "actual_rows": plan.get('Actual Rows', 0),
                    "shared_blocks_read": plan.get('Shared Read Blocks', 0),
                    "shared_blocks_hit": plan.get('Shared Blocks Hit', 0)
                }
            elif self.database_type == 'mysql':
                cursor.execute(f"EXPLAIN FORMAT=JSON {query}")
                result = cursor.fetchone()[0]
                
                # Handle different MySQL EXPLAIN JSON formats
                if isinstance(result, str):
                    result = json.loads(result)
                
                plan = result['query_block']['table']
                
                # For MySQL, we need to run the actual query to measure time
                start_time = time.time()
                cursor.execute(query)
                cursor.fetchall()  # Consume all results
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                return {
                    "node_type": plan.get('access_type', 'UNKNOWN'),
                    "total_cost": 0,  # MySQL doesn't use cost model
                    "execution_time_ms": execution_time,
                    "rows_examined": plan.get('rows_examined_per_scan', 0),
                    "filtered": plan.get('filtered', 0)
                }
        except Exception as e:
            print(f"❌ Error getting performance metrics: {e}")
            return {
                "node_type": "ERROR",
                "total_cost": 0,
                "execution_time_ms": 0,
                "error": str(e)
            }
    
    def apply_recommendation(self, cursor, recommendation: str) -> bool:
        """
        Apply a database recommendation.
        
        Args:
            cursor: Database cursor
            recommendation: SQL command to execute
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"🔧 Applying: {recommendation}")
            
            # Check if index already exists and drop it first
            if recommendation.upper().strip().startswith('CREATE INDEX'):
                index_name = self._extract_index_name(recommendation)
                if index_name:
                    self._drop_index_if_exists(cursor, index_name)
            
            cursor.execute(recommendation)
            
            # Track the change for cleanup
            self.applied_changes.append(recommendation)
            print("✅ Recommendation applied successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to apply recommendation: {e}")
            return False
    
    def _extract_index_name(self, recommendation: str) -> str:
        """Extract index name from CREATE INDEX statement."""
        match = re.search(r'CREATE\s+INDEX\s+(\w+)', recommendation.upper())
        return match.group(1) if match else None
    
    def _drop_index_if_exists(self, cursor, index_name: str):
        """Drop index if it exists."""
        try:
            if self.database_type == 'mysql':
                cursor.execute(f"DROP INDEX {index_name} ON orders;")
            else:
                cursor.execute(f"DROP INDEX IF EXISTS {index_name};")
            print(f"🗑️  Dropped existing index: {index_name}")
        except Exception as e:
            # Index doesn't exist, which is fine
            pass
    
    def cleanup_changes(self, cursor) -> bool:
        """
        Clean up applied changes.
        
        Args:
            cursor: Database cursor
            
        Returns:
            True if successful, False otherwise
        """
        success = True
        for change in reversed(self.applied_changes):  # Reverse order for proper cleanup
            try:
                cleanup_command = self._generate_cleanup_command(change)
                if cleanup_command:
                    print(f"🧹 Cleaning up: {cleanup_command}")
                    cursor.execute(cleanup_command)
                    print("✅ Cleanup successful")
            except Exception as e:
                print(f"❌ Cleanup failed for '{change}': {e}")
                success = False
        
        self.applied_changes.clear()
        return success
    
    def _generate_cleanup_command(self, original_command: str) -> Optional[str]:
        """
        Generate cleanup command from original command.
        
        Args:
            original_command: Original SQL command
            
        Returns:
            Cleanup command or None if not applicable
        """
        original_upper = original_command.upper().strip()
        
        if original_upper.startswith('CREATE INDEX'):
            # Extract index name
            match = re.search(r'CREATE\s+INDEX\s+(\w+)', original_upper)
            if match:
                index_name = match.group(1)
                if self.database_type == 'mysql':
                    return f"DROP INDEX {index_name} ON orders;"
                else:
                    return f"DROP INDEX IF EXISTS {index_name};"
        
        elif original_upper.startswith('DROP INDEX'):
            # For DROP INDEX commands, we need to recreate the index
            # This is a simplified approach - in practice, you'd need to store the original CREATE statement
            if 'orders_pkey' in original_upper:
                return "CREATE INDEX orders_pkey ON orders (id);"  # Recreate primary key
            return None
        
        elif original_upper.startswith('CREATE TABLE'):
            # Extract table name
            match = re.search(r'CREATE\s+TABLE\s+(\w+)', original_upper)
            if match:
                table_name = match.group(1)
                return f"DROP TABLE IF EXISTS {table_name};"
        
        elif original_upper.startswith('ALTER TABLE'):
            # For ALTER TABLE, we might need more complex cleanup
            # For now, just log that manual cleanup might be needed
            print(f"⚠️  Manual cleanup may be required for: {original_command}")
            return None
        
        return None
    
    def validate_recommendation(self, query: str, recommendation: str, iterations: int = 3) -> Dict[str, Any]:
        """
        Validate a recommendation by measuring performance before and after.
        
        Args:
            query: SQL query to test
            recommendation: Recommendation to validate
            iterations: Number of iterations to run for more accurate results
            
        Returns:
            Validation results dictionary
        """
        print(f"\n{'='*60}")
        print(f"🔍 VALIDATING RECOMMENDATION")
        print(f"{'='*60}")
        print(f"Query: {query}")
        print(f"Recommendation: {recommendation}")
        print(f"Database: {self.database_type.upper()}")
        print(f"Iterations: {iterations}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.connect()
        
        try:
            with self.connection.cursor() as cur:
                # 1. Baseline: Measure performance before changes
                print(f"\n📊 [BASELINE] Measuring performance before applying recommendation...")
                before_metrics = []
                
                for i in range(iterations):
                    print(f"  Iteration {i+1}/{iterations}...")
                    metrics = self.get_performance_metrics(cur, query)
                    before_metrics.append(metrics)
                    time.sleep(0.1)  # Small delay between iterations
                
                # Calculate average baseline metrics
                avg_before = self._calculate_average_metrics(before_metrics)
                print(f"  ✅ Baseline: {avg_before['node_type']} - {avg_before['execution_time_ms']:.2f}ms avg")
                
                # 2. Apply recommendation
                print(f"\n🔧 [APPLY] Applying recommendation...")
                if not self.apply_recommendation(cur, recommendation):
                    return {
                        "success": False,
                        "error": "Failed to apply recommendation",
                        "baseline_metrics": avg_before
                    }
                
                # 3. After: Measure performance after changes
                print(f"\n📊 [AFTER] Measuring performance after applying recommendation...")
                after_metrics = []
                
                for i in range(iterations):
                    print(f"  Iteration {i+1}/{iterations}...")
                    metrics = self.get_performance_metrics(cur, query)
                    after_metrics.append(metrics)
                    time.sleep(0.1)
                
                # Calculate average after metrics
                avg_after = self._calculate_average_metrics(after_metrics)
                print(f"  ✅ After: {avg_after['node_type']} - {avg_after['execution_time_ms']:.2f}ms avg")
                
                # 4. Calculate improvements
                improvement = self._calculate_improvement(avg_before, avg_after)
                
                # 5. Generate validation report
                validation_result = {
                    "success": True,
                    "query": query,
                    "recommendation": recommendation,
                    "database_type": self.database_type,
                    "iterations": iterations,
                    "baseline_metrics": avg_before,
                    "after_metrics": avg_after,
                    "improvement": improvement,
                    "all_baseline_metrics": before_metrics,
                    "all_after_metrics": after_metrics,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 6. Display results
                self._display_validation_results(validation_result)
                
                return validation_result
                
        finally:
            # 7. Cleanup
            print(f"\n🧹 [CLEANUP] Cleaning up applied changes...")
            try:
                with self.connection.cursor() as cur:
                    self.cleanup_changes(cur)
            except Exception as e:
                print(f"❌ Cleanup failed: {e}")
            
            self.disconnect()
    
    def _calculate_average_metrics(self, metrics_list: list) -> Dict[str, Any]:
        """Calculate average metrics from multiple measurements."""
        if not metrics_list:
            return {}
        
        avg_metrics = {}
        for key in metrics_list[0].keys():
            if key == 'error':
                continue
            try:
                values = [m.get(key, 0) for m in metrics_list if key in m]
                if values:
                    avg_metrics[key] = sum(values) / len(values)
            except (TypeError, ValueError):
                # For non-numeric values, take the most common one
                values = [m.get(key) for m in metrics_list if key in m]
                if values:
                    avg_metrics[key] = max(set(values), key=values.count)
        
        return avg_metrics
    
    def _calculate_improvement(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance improvement metrics."""
        improvement = {}
        
        # Execution time improvement
        if 'execution_time_ms' in before and 'execution_time_ms' in after:
            time_delta = before['execution_time_ms'] - after['execution_time_ms']
            time_percent = (time_delta / before['execution_time_ms']) * 100 if before['execution_time_ms'] > 0 else 0
            improvement['execution_time_delta_ms'] = time_delta
            improvement['execution_time_percent_improvement'] = time_percent
        
        # Cost improvement (PostgreSQL only)
        if 'total_cost' in before and 'total_cost' in after and before['total_cost'] > 0:
            cost_delta = before['total_cost'] - after['total_cost']
            cost_percent = (cost_delta / before['total_cost']) * 100
            improvement['cost_delta'] = cost_delta
            improvement['cost_percent_improvement'] = cost_percent
        
        # Plan type change
        if 'node_type' in before and 'node_type' in after:
            improvement['plan_change'] = f"{before['node_type']} → {after['node_type']}"
            improvement['plan_improved'] = self._is_plan_improvement(before['node_type'], after['node_type'])
        
        # Overall assessment
        improvement['overall_improvement'] = self._assess_overall_improvement(improvement)
        
        return improvement
    
    def _is_plan_improvement(self, before_type: str, after_type: str) -> bool:
        """Determine if the plan change represents an improvement."""
        # Define improvement patterns
        improvements = [
            ('Seq Scan', 'Index Scan'),
            ('Seq Scan', 'Bitmap Heap Scan'),
            ('ALL', 'ref'),  # MySQL
            ('ALL', 'range'),  # MySQL
        ]
        
        return (before_type, after_type) in improvements
    
    def _assess_overall_improvement(self, improvement: Dict[str, Any]) -> str:
        """Assess overall improvement level."""
        time_improvement = improvement.get('execution_time_percent_improvement', 0)
        plan_improved = improvement.get('plan_improved', False)
        
        if plan_improved and time_improvement > 50:
            return "EXCELLENT"
        elif plan_improved and time_improvement > 20:
            return "GOOD"
        elif time_improvement > 10:
            return "MODERATE"
        elif time_improvement > 0:
            return "MINIMAL"
        else:
            return "NEGATIVE"
    
    def _display_validation_results(self, result: Dict[str, Any]):
        """Display validation results in a formatted way."""
        print(f"\n{'='*60}")
        print(f"📋 VALIDATION RESULTS")
        print(f"{'='*60}")
        
        if not result['success']:
            print(f"❌ VALIDATION FAILED: {result.get('error', 'Unknown error')}")
            return
        
        improvement = result['improvement']
        baseline = result['baseline_metrics']
        after = result['after_metrics']
        
        print(f"✅ VALIDATION SUCCESSFUL")
        print(f"")
        print(f"📊 Performance Metrics:")
        print(f"  Before: {baseline.get('node_type', 'N/A')} - {baseline.get('execution_time_ms', 0):.2f}ms")
        print(f"  After:  {after.get('node_type', 'N/A')} - {after.get('execution_time_ms', 0):.2f}ms")
        print(f"")
        print(f"📈 Improvements:")
        if 'execution_time_delta_ms' in improvement:
            print(f"  Time Improvement: {improvement['execution_time_delta_ms']:.2f}ms ({improvement['execution_time_percent_improvement']:.1f}%)")
        if 'cost_delta' in improvement:
            print(f"  Cost Improvement: {improvement['cost_delta']:.2f} ({improvement['cost_percent_improvement']:.1f}%)")
        if 'plan_change' in improvement:
            print(f"  Plan Change: {improvement['plan_change']}")
        print(f"  Overall Assessment: {improvement['overall_improvement']}")
        print(f"")
        print(f"🎯 Recommendation: {'✅ KEEP' if improvement['overall_improvement'] in ['EXCELLENT', 'GOOD', 'MODERATE'] else '❌ REJECT'}")

def main():
    """Main function to run validation harness."""
    print("🔧 Database Performance Validation Harness")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "database": "postgresql",
            "query": "SELECT * FROM orders WHERE customer_id = 42;",
            "recommendation": "CREATE INDEX idx_orders_customer_id ON orders (customer_id);"
        },
        {
            "database": "mysql", 
            "query": "SELECT * FROM orders WHERE customer_id = 42;",
            "recommendation": "CREATE INDEX idx_orders_customer_id ON orders (customer_id);"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}/{len(test_cases)}")
        
        harness = ValidationHarness(test_case["database"])
        result = harness.validate_recommendation(
            test_case["query"],
            test_case["recommendation"],
            iterations=3
        )
        results.append(result)
    
    # Save results
    with open('artifacts/validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: artifacts/validation_results.json")
    
    # Summary
    successful = sum(1 for r in results if r['success'])
    print(f"\n📊 Summary: {successful}/{len(results)} validations successful")

if __name__ == '__main__':
    main()
