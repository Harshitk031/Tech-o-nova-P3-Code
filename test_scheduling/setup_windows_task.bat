@echo off
echo Setting up Windows Task Scheduler for Database Performance Collection
schtasks /create /tn "DatabasePerformanceCollection" /tr "D:\e6data_P3\scripts\run_collection.bat" /sc minute /mo 15 /ru SYSTEM
echo Task created successfully!
pause
