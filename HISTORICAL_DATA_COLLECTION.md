# 📊 Historical Data Collection and Trending Analysis

## 🎯 **Overview**

The Database Performance Analysis Tool now includes a comprehensive historical data collection system that captures performance metrics over time, enabling trend analysis and long-term performance monitoring.

## 🏗️ **Architecture**

### **Components:**
1. **Historical Database Schema** - PostgreSQL database for storing performance snapshots
2. **Collection Scripts** - Automated data collection from PostgreSQL and MySQL
3. **Analysis Scripts** - Trend analysis and reporting tools
4. **Scheduling System** - Automated collection via cron/systemd/Windows Task Scheduler

### **Data Flow:**
```
Target Databases → Collection Scripts → Historical Database → Analysis Scripts → Reports
```

## 📋 **Database Schema**

### **Tables Created:**
- `query_snapshots` - PostgreSQL query performance data
- `slow_log_summary` - MySQL slow query summaries  
- `index_usage_snapshots` - Index usage statistics
- `query_plan_snapshots` - Query execution plans

### **Views Created:**
- `query_performance_trends` - Hourly aggregated query performance
- `index_usage_trends` - Hourly aggregated index usage

## 🚀 **Setup Instructions**

### **Step 1: Create Historical Database**
```bash
# Create the historical database
psql -c "CREATE DATABASE performance_history;"

# Run the schema setup
psql -d performance_history -f samples/historical_schema.sql
```

### **Step 2: Configure Environment Variables**
```bash
# Set database credentials (if not using defaults)
export POSTGRES_PASSWORD="your_password"
export MYSQL_PASSWORD="your_password"
```

### **Step 3: Test Collection**
```bash
# Test individual collectors
python scripts/collect_postgres_stats.py
python scripts/collect_mysql_stats.py

# Test master collector
python scripts/collect_all_stats.py
```

### **Step 4: Set Up Scheduling**
```bash
# Create scheduling configuration
python scripts/setup_scheduling.py --interval 15

# Follow the platform-specific instructions provided
```

## 📊 **Collection Scripts**

### **1. PostgreSQL Stats Collection (`collect_postgres_stats.py`)**

**Purpose:** Collects query performance statistics from `pg_stat_statements`

**Features:**
- Query execution times and call counts
- Index usage statistics
- Buffer hit ratios
- Block I/O statistics

**Usage:**
```bash
python scripts/collect_postgres_stats.py [options]

Options:
  --target-db TARGET_DB     Target database name (default: postgres)
  --historical-db HISTORICAL_DB  Historical database name (default: performance_history)
  --verbose, -v             Verbose output
```

### **2. MySQL Stats Collection (`collect_mysql_stats.py`)**

**Purpose:** Collects slow query statistics from MySQL performance schema

**Features:**
- Slow query summaries
- Query execution times and frequencies
- Index usage patterns
- Row examination statistics

**Usage:**
```bash
python scripts/collect_mysql_stats.py [options]

Options:
  --target-db TARGET_DB     Target database name (default: test)
  --historical-db HISTORICAL_DB  Historical database name (default: performance_history)
  --verbose, -v             Verbose output
```

### **3. Master Collection Script (`collect_all_stats.py`)**

**Purpose:** Runs both PostgreSQL and MySQL collection scripts

**Usage:**
```bash
python scripts/collect_all_stats.py [options]

Options:
  --postgres-db POSTGRES_DB     PostgreSQL database name (default: postgres)
  --mysql-db MYSQL_DB           MySQL database name (default: test)
  --historical-db HISTORICAL_DB Historical database name (default: performance_history)
  --skip-postgres               Skip PostgreSQL collection
  --skip-mysql                  Skip MySQL collection
  --verbose, -v                 Verbose output
```

## 📈 **Analysis Scripts**

### **Trend Analysis (`analyze_trends.py`)**

**Purpose:** Analyzes historical data to identify performance trends and patterns

**Features:**
- Query performance trends over time
- Slowest queries identification
- Unused index detection
- Performance summary reports
- JSON export for further analysis

**Usage:**
```bash
python scripts/analyze_trends.py [options]

Options:
  --hours HOURS             Hours of data to analyze (default: 24)
  --output OUTPUT           Output file for JSON export
  --report                  Generate text report
  --historical-db HISTORICAL_DB  Historical database name (default: performance_history)
```

**Examples:**
```bash
# Generate text report for last 24 hours
python scripts/analyze_trends.py --report

# Generate report for last 7 days
python scripts/analyze_trends.py --report --hours 168

# Export trends to JSON
python scripts/analyze_trends.py --output trends.json --hours 24
```

## ⏰ **Scheduling and Automation**

### **Scheduling Setup (`setup_scheduling.py`)**

**Purpose:** Creates platform-specific scheduling configurations

**Supported Platforms:**
- **Linux/macOS:** Cron jobs and systemd timers
- **Windows:** Task Scheduler

**Usage:**
```bash
python scripts/setup_scheduling.py [options]

Options:
  --interval INTERVAL       Collection interval in minutes (default: 15)
  --script SCRIPT           Script to schedule (default: collect_all_stats.py)
  --output-dir OUTPUT_DIR   Output directory for configuration files
```

### **Linux/macOS Setup:**
```bash
# Create cron job
python scripts/setup_scheduling.py --interval 15
crontab crontab_entry.txt

# Or use systemd timer
sudo cp db-performance-collection.timer /etc/systemd/system/
sudo cp db-performance-collection.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable db-performance-collection.timer
sudo systemctl start db-performance-collection.timer
```

### **Windows Setup:**
```bash
# Create Task Scheduler configuration
python scripts/setup_scheduling.py --interval 15

# Run as Administrator to install
setup_windows_task.bat
```

## 📊 **Data Analysis Examples**

### **1. View Performance Trends**
```bash
# Generate comprehensive report
python scripts/analyze_trends.py --report --hours 24
```

**Sample Output:**
```
================================================================================
📊 DATABASE PERFORMANCE TREND ANALYSIS
================================================================================
Analysis Period: Last 24 hours
Generated: 2025-09-12 18:00:00

📈 PERFORMANCE SUMMARY
----------------------------------------
Unique Queries: 15
Total Calls: 1,250
Average Execution Time: 45.67 ms
Maximum Execution Time: 1,250.00 ms

Unique Indexes: 8
Average Index Usage: 156.25

🐌 SLOWEST QUERIES
----------------------------------------
1. postgres - 1250.00 ms avg
   Calls: 25
   Query: SELECT * FROM orders WHERE customer_id = ?...

2. postgres - 890.50 ms avg
   Calls: 150
   Query: SELECT COUNT(*) FROM orders WHERE created_at > ?...
```

### **2. Export Data for Analysis**
```bash
# Export to JSON for further analysis
python scripts/analyze_trends.py --output trends.json --hours 168
```

### **3. Monitor Specific Time Periods**
```bash
# Analyze last 7 days
python scripts/analyze_trends.py --report --hours 168

# Analyze last 30 days
python scripts/analyze_trends.py --report --hours 720
```

## 🔧 **Configuration and Customization**

### **Collection Intervals**
- **High-frequency monitoring:** 5-15 minutes
- **Standard monitoring:** 15-30 minutes  
- **Low-frequency monitoring:** 1-6 hours

### **Data Retention**
- **Default:** 30 days (configurable in schema)
- **Cleanup function:** `cleanup_old_snapshots()`
- **Manual cleanup:** `SELECT cleanup_old_snapshots();`

### **Database Configuration**
All scripts use the centralized configuration system:
- Environment variables for credentials
- Configurable database names
- Automatic connection string generation

## 📈 **Monitoring and Alerting**

### **Key Metrics to Monitor:**
1. **Query Performance Trends**
   - Average execution time trends
   - Slowest queries over time
   - Query frequency patterns

2. **Index Usage Patterns**
   - Unused index identification
   - Index usage trends
   - Storage optimization opportunities

3. **System Health Indicators**
   - Collection script success rates
   - Data freshness
   - Storage usage

### **Recommended Alerts:**
- Collection script failures
- Significant performance degradation
- Unused indexes consuming storage
- Database connection issues

## 🛠️ **Troubleshooting**

### **Common Issues:**

1. **Collection Scripts Failing**
   - Check database connectivity
   - Verify historical database exists
   - Check permissions on historical database

2. **Missing Data**
   - Verify scheduling is working
   - Check collection script logs
   - Ensure target databases are accessible

3. **Performance Issues**
   - Monitor historical database size
   - Run cleanup functions regularly
   - Consider adjusting collection intervals

### **Debug Commands:**
```bash
# Test individual collectors
python scripts/collect_postgres_stats.py --verbose
python scripts/collect_mysql_stats.py --verbose

# Check historical database
psql -d performance_history -c "SELECT COUNT(*) FROM query_snapshots;"

# View recent collections
psql -d performance_history -c "SELECT captured_at, COUNT(*) FROM query_snapshots GROUP BY captured_at ORDER BY captured_at DESC LIMIT 10;"
```

## 🎯 **Best Practices**

### **Production Deployment:**
1. **Start with longer intervals** (30-60 minutes) and adjust based on system load
2. **Monitor historical database size** and set up automated cleanup
3. **Use separate database instance** for historical data to avoid impact on production
4. **Set up monitoring** for collection script health
5. **Regular backup** of historical database

### **Data Analysis:**
1. **Baseline establishment** - Run for at least 1 week before making decisions
2. **Trend analysis** - Look for patterns over multiple time periods
3. **Correlation analysis** - Compare query performance with system metrics
4. **Regular review** - Weekly/monthly analysis of trends and recommendations

## 🚀 **Next Steps**

1. **Set up the historical database** using the provided schema
2. **Configure collection scripts** for your environment
3. **Set up scheduling** for automated data collection
4. **Establish monitoring** and alerting for the collection system
5. **Begin trend analysis** after collecting data for a few days
6. **Integrate with existing monitoring** systems and dashboards

The historical data collection system provides a solid foundation for long-term database performance monitoring and optimization! 📊✨
