#!/usr/bin/env python3
"""
Scheduling Setup Script
Creates cron jobs and systemd timers for automated data collection.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def create_cron_job(script_path: str, interval_minutes: int = 15) -> str:
    """Create a cron job entry for the collection script."""
    python_path = sys.executable
    cron_entry = f"*/{interval_minutes} * * * * {python_path} {script_path} >> /var/log/db_performance_collection.log 2>&1"
    return cron_entry

def create_systemd_timer(script_path: str, interval_minutes: int = 15) -> str:
    """Create a systemd timer configuration."""
    script_name = Path(script_path).stem
    timer_content = f"""[Unit]
Description=Database Performance Collection Timer
Requires=db-performance-collection.service

[Timer]
OnCalendar=*:0/{interval_minutes}
Persistent=true

[Install]
WantedBy=timers.target
"""
    
    service_content = f"""[Unit]
Description=Database Performance Collection Service

[Service]
Type=oneshot
ExecStart={sys.executable} {script_path}
User=postgres
Group=postgres
"""
    
    return timer_content, service_content

def create_windows_task(script_path: str, interval_minutes: int = 15) -> str:
    """Create a Windows Task Scheduler command."""
    python_path = sys.executable
    task_name = "DatabasePerformanceCollection"
    
    # Create a batch file
    batch_content = f"""@echo off
cd /d "{os.path.dirname(script_path)}"
{python_path} {os.path.basename(script_path)}
"""
    
    batch_file = os.path.join(os.path.dirname(script_path), "run_collection.bat")
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    # Create schtasks command
    schtasks_cmd = f"""schtasks /create /tn "{task_name}" /tr "{batch_file}" /sc minute /mo {interval_minutes} /ru SYSTEM"""
    
    return schtasks_cmd

def main():
    """Main function for setting up scheduling."""
    parser = argparse.ArgumentParser(description="Set up automated data collection scheduling")
    parser.add_argument('--interval', type=int, default=15, help='Collection interval in minutes')
    parser.add_argument('--script', default='collect_all_stats.py', help='Script to schedule')
    parser.add_argument('--output-dir', default='.', help='Output directory for configuration files')
    
    args = parser.parse_args()
    
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), args.script))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("⏰ Setting up Database Performance Collection Scheduling")
    print("=" * 60)
    print(f"Script: {script_path}")
    print(f"Interval: {args.interval} minutes")
    print(f"Platform: {platform.system()}")
    print("")
    
    system = platform.system().lower()
    
    if system == "linux" or system == "darwin":  # Linux or macOS
        print("Linux/macOS: Creating Linux/macOS scheduling configuration")
        print("-" * 40)
        
        # Create cron job
        cron_entry = create_cron_job(script_path, args.interval)
        cron_file = output_dir / "crontab_entry.txt"
        
        with open(cron_file, 'w') as f:
            f.write(f"# Database Performance Collection\n")
            f.write(f"# Run every {args.interval} minutes\n")
            f.write(f"{cron_entry}\n")
        
        print(f"✅ Cron entry created: {cron_file}")
        print(f"   To install: crontab {cron_file}")
        print("")
        
        # Create systemd timer
        timer_content, service_content = create_systemd_timer(script_path, args.interval)
        
        timer_file = output_dir / "db-performance-collection.timer"
        service_file = output_dir / "db-performance-collection.service"
        
        with open(timer_file, 'w') as f:
            f.write(timer_content)
        
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"✅ Systemd timer created: {timer_file}")
        print(f"✅ Systemd service created: {service_file}")
        print("")
        print("To install systemd timer:")
        print(f"  sudo cp {timer_file} /etc/systemd/system/")
        print(f"  sudo cp {service_file} /etc/systemd/system/")
        print("  sudo systemctl daemon-reload")
        print("  sudo systemctl enable db-performance-collection.timer")
        print("  sudo systemctl start db-performance-collection.timer")
        
    elif system == "windows":
        print("Windows: Creating Windows scheduling configuration")
        print("-" * 40)
        
        # Create Windows Task Scheduler command
        schtasks_cmd = create_windows_task(script_path, args.interval)
        
        batch_file = output_dir / "setup_windows_task.bat"
        with open(batch_file, 'w') as f:
            f.write(f"@echo off\n")
            f.write(f"echo Setting up Windows Task Scheduler for Database Performance Collection\n")
            f.write(f"{schtasks_cmd}\n")
            f.write(f"echo Task created successfully!\n")
            f.write(f"pause\n")
        
        print(f"✅ Windows task setup created: {batch_file}")
        print(f"   Run as Administrator to install the scheduled task")
        print("")
        print("Manual installation command:")
        print(f"  {schtasks_cmd}")
        
    else:
        print(f"❌ Unsupported platform: {system}")
        print("   Please set up scheduling manually")
        sys.exit(1)
    
    print("")
    print("📋 Next Steps:")
    print("1. Install the scheduling configuration using the commands above")
    print("2. Verify the collection is running: check logs or run manually")
    print("3. Set up monitoring for the collection process")
    print("4. Configure log rotation for collection logs")
    print("")
    print("🔍 Monitoring Commands:")
    print("  # View recent trends")
    print("  python scripts/analyze_trends.py --report")
    print("")
    print("  # Export trends to JSON")
    print("  python scripts/analyze_trends.py --output trends.json")
    print("")
    print("  # Run collection manually")
    print(f"  python {script_path}")

if __name__ == '__main__':
    import argparse
    main()
