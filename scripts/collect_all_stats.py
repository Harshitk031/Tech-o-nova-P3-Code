#!/usr/bin/env python3
"""
Master Statistics Collection Script
Runs both PostgreSQL and MySQL statistics collection.
"""

import sys
import os
import subprocess
import argparse
from datetime import datetime

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_collector(script_name: str, args: list = None) -> bool:
    """Run a collection script and return success status."""
    if args is None:
        args = []
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    cmd = [sys.executable, script_path] + args
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {script_name} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {script_name} failed with exit code {e.returncode}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False
    except Exception as e:
        print(f"❌ {script_name} failed with exception: {e}")
        return False

def main():
    """Main function for collecting all statistics."""
    parser = argparse.ArgumentParser(description="Collect all database performance statistics")
    parser.add_argument('--postgres-db', default='postgres', help='PostgreSQL database name')
    parser.add_argument('--mysql-db', default='test', help='MySQL database name')
    parser.add_argument('--historical-db', default='performance_history', help='Historical database name')
    parser.add_argument('--skip-postgres', action='store_true', help='Skip PostgreSQL collection')
    parser.add_argument('--skip-mysql', action='store_true', help='Skip MySQL collection')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    print("🚀 Starting Database Performance Statistics Collection")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Historical Database: {args.historical_db}")
    print("")
    
    results = {}
    
    # Collect PostgreSQL statistics
    if not args.skip_postgres:
        print("📊 Collecting PostgreSQL Statistics")
        print("-" * 40)
        postgres_args = [
            '--target-db', args.postgres_db,
            '--historical-db', args.historical_db
        ]
        if args.verbose:
            postgres_args.append('--verbose')
        
        results['postgres'] = run_collector('collect_postgres_stats.py', postgres_args)
        print("")
    else:
        print("⏭️  Skipping PostgreSQL collection")
        results['postgres'] = True
    
    # Collect MySQL statistics
    if not args.skip_mysql:
        print("📊 Collecting MySQL Statistics")
        print("-" * 40)
        mysql_args = [
            '--target-db', args.mysql_db,
            '--historical-db', args.historical_db
        ]
        if args.verbose:
            mysql_args.append('--verbose')
        
        results['mysql'] = run_collector('collect_mysql_stats.py', mysql_args)
        print("")
    else:
        print("⏭️  Skipping MySQL collection")
        results['mysql'] = True
    
    # Summary
    print("📋 Collection Summary")
    print("=" * 60)
    postgres_status = "✅ SUCCESS" if results['postgres'] else "❌ FAILED"
    mysql_status = "✅ SUCCESS" if results['mysql'] else "❌ FAILED"
    
    print(f"PostgreSQL: {postgres_status}")
    print(f"MySQL: {mysql_status}")
    
    overall_success = results['postgres'] and results['mysql']
    if overall_success:
        print("\n🎉 All statistics collection completed successfully!")
        print("💡 Run 'python scripts/analyze_trends.py --report' to view trends")
        sys.exit(0)
    else:
        print("\n⚠️  Some collections failed - check the output above")
        sys.exit(1)

if __name__ == '__main__':
    main()
