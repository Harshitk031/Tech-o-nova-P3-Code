#!/usr/bin/env python3
"""
Setup script for Database Performance Analysis Tool
Provides easy installation and setup options.
"""

import os
import sys
import subprocess
import argparse

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"   Error output: {e.stderr}")
        return False

def install_requirements(requirements_file):
    """Install requirements from specified file."""
    if not os.path.exists(requirements_file):
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    return run_command(f"pip install -r {requirements_file}", f"Installing {requirements_file}")

def start_databases():
    """Start Docker databases."""
    return run_command("docker-compose up -d", "Starting database containers")

def initialize_databases():
    """Initialize databases with sample data."""
    print("🔄 Initializing databases with sample data...")
    
    # PostgreSQL initialization
    postgres_cmd = 'Get-Content samples/postgres.sql | docker exec -i e6data_p3-postgres-1 psql -U postgres'
    if not run_command(postgres_cmd, "Initializing PostgreSQL"):
        return False
    
    # MySQL initialization
    mysql_cmd = 'Get-Content samples/mysql.sql | docker exec -i e6data_p3-mysql-1 mysql -u root -pmysql'
    if not run_command(mysql_cmd, "Initializing MySQL"):
        return False
    
    return True

def verify_installation():
    """Run installation verification."""
    return run_command("python verify_installation.py", "Verifying installation")

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Setup Database Performance Analysis Tool")
    parser.add_argument(
        '--requirements',
        choices=['minimal', 'full', 'dev'],
        default='minimal',
        help='Which requirements to install (default: minimal)'
    )
    parser.add_argument(
        '--skip-databases',
        action='store_true',
        help='Skip database setup'
    )
    parser.add_argument(
        '--skip-verification',
        action='store_true',
        help='Skip installation verification'
    )
    
    args = parser.parse_args()
    
    print("🚀 Database Performance Analysis Tool Setup")
    print("=" * 50)
    
    # Map requirements choices to files
    requirements_map = {
        'minimal': 'requirements-minimal.txt',
        'full': 'requirements.txt',
        'dev': 'requirements-dev.txt'
    }
    
    requirements_file = requirements_map[args.requirements]
    
    # Step 1: Install requirements
    print(f"\n📦 Step 1: Installing {args.requirements} requirements...")
    if not install_requirements(requirements_file):
        print("❌ Setup failed at requirements installation")
        sys.exit(1)
    
    # Step 2: Start databases (if not skipped)
    if not args.skip_databases:
        print("\n🐳 Step 2: Starting database containers...")
        if not start_databases():
            print("❌ Setup failed at database startup")
            sys.exit(1)
        
        print("\n📊 Step 3: Initializing databases...")
        if not initialize_databases():
            print("❌ Setup failed at database initialization")
            sys.exit(1)
    else:
        print("\n⏭️  Skipping database setup")
    
    # Step 3: Verify installation (if not skipped)
    if not args.skip_verification:
        print("\n🔍 Step 4: Verifying installation...")
        if not verify_installation():
            print("⚠️  Installation verification had issues, but setup completed")
    else:
        print("\n⏭️  Skipping installation verification")
    
    # Success message
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📚 Next Steps:")
    print("   1. Run analysis: python analyze_db.py postgres \"SELECT * FROM orders WHERE customer_id = 42;\"")
    print("   2. See help: python analyze_db.py --help")
    print("   3. Run demo: python final_demo.py")
    print("\n📖 Documentation: README.md")

if __name__ == '__main__':
    main()
