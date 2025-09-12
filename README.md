# Database Performance Analysis Tool

A comprehensive database performance analysis tool that identifies optimization opportunities in PostgreSQL and MySQL databases through query plan analysis, unused index detection, and automated recommendations.

## Features

### 🔍 Query Analysis
- **SQL Feature Extraction**: Automatically extracts columns from WHERE clauses using SQLGlot
- **Query Plan Parsing**: Parses EXPLAIN output from both PostgreSQL and MySQL
- **Performance Metrics**: Analyzes execution time, cost, row counts, and buffer usage

### 📊 Unused Index Detection
- **PostgreSQL**: Queries `pg_stat_user_indexes` to find indexes with zero scan count
- **MySQL**: Uses `sys.schema_unused_indexes` to identify unused indexes
- **Size Analysis**: Reports index sizes to help prioritize removal candidates

### 🎯 Automated Recommendations
- **Missing Index Detection**: Identifies sequential scans on filtered queries
- **Inefficient Sort Detection**: Flags external merge sorts that could benefit from indexes
- **Statistics Issues**: Detects outdated statistics causing poor query planning
- **Unused Index Removal**: Suggests removal of unused indexes to save space

### 📈 Scoring System
- **Confidence Scores**: 0.0-1.0 scale indicating recommendation certainty
- **Impact Tiers**: Low/Medium/High classification of expected performance improvement
- **Evidence-Based**: Uses plan data, statistics, and hypothetical index simulations

## Installation

### Prerequisites
- Python 3.7+
- Docker and Docker Compose
- PostgreSQL 13+ (via Docker)
- MySQL 8.0+ (via Docker)

### Requirements Files
The project includes three requirements files for different use cases:

- **`requirements-minimal.txt`**: Core dependencies only (psycopg2-binary, mysql-connector-python, sqlglot)
- **`requirements.txt`**: Full requirements including optional tools (pandas, numpy, colorama, etc.)
- **`requirements-dev.txt`**: Development dependencies including testing, linting, and documentation tools

### Setup

#### Quick Setup (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd e6data_P3

# Run automated setup
python setup.py --requirements minimal

# OR for full setup with all optional tools
python setup.py --requirements full

# OR for development setup
python setup.py --requirements dev
```

#### Manual Setup
1. Clone the repository:
```bash
git clone <repository-url>
cd e6data_P3
```

2. Install Python dependencies:
```bash
# Install minimal requirements (core functionality only)
pip install -r requirements-minimal.txt

# OR install full requirements (includes optional tools)
pip install -r requirements.txt

# OR install development requirements (includes testing and dev tools)
pip install -r requirements-dev.txt
```

3. Start the database containers:
```bash
docker-compose up -d
```

4. Initialize the databases with sample data:
```bash
# PostgreSQL
Get-Content samples/postgres.sql | docker exec -i e6data_p3-postgres-1 psql -U postgres

# MySQL
Get-Content samples/mysql.sql | docker exec -i e6data_p3-mysql-1 mysql -u root -pmysql
```

5. Verify installation:
```bash
python verify_installation.py
```

## Usage

### Command Line Interface

#### Analyze a PostgreSQL Query
```bash
python analyze_db.py postgres "SELECT * FROM orders WHERE customer_id = 42;"
```

#### Analyze a MySQL Query
```bash
python analyze_db.py mysql "SELECT * FROM orders WHERE customer_id = 42;"
```

#### Analyze Both Databases
```bash
python analyze_db.py both "SELECT * FROM orders WHERE customer_id = 42;"
```

#### Save Results to File
```bash
python analyze_db.py postgres "SELECT * FROM orders WHERE customer_id = 42;" --output results.txt
```

#### JSON Output Format
```bash
python analyze_db.py postgres "SELECT * FROM orders WHERE customer_id = 42;" --format json
```

### Individual Components

#### Find Unused Indexes
```bash
python scripts/find_unused_indexes.py
```

#### Run Comprehensive Analysis
```bash
python src/analysis/comprehensive_analysis.py
```

#### Test Rules Engine
```bash
python src/analysis/rules_engine.py
```

#### Test Scoring System
```bash
python src/analysis/scoring.py
```

## Project Structure

```
e6data_P3/
├── analyze_db.py                          # Main CLI interface
├── docker-compose.yml                     # Database containers
├── samples/
│   ├── postgres.sql                       # PostgreSQL sample data
│   └── mysql.sql                          # MySQL sample data
├── src/
│   ├── analysis/
│   │   ├── comprehensive_analysis.py      # Integrated analysis pipeline
│   │   ├── integrated_pipeline.py        # Basic analysis pipeline
│   │   ├── rules_engine.py               # Optimization rules
│   │   ├── scoring.py                    # Confidence and impact scoring
│   │   └── sql_features.py               # SQL parsing and feature extraction
│   └── parsers/
│       ├── postgres_plan.py              # PostgreSQL plan parser
│       └── mysql_plan.py                 # MySQL plan parser
├── scripts/
│   ├── find_unused_indexes.py            # Unused index detection
│   ├── hypopg_simulate.py                # Hypothetical index simulation
│   └── real_index_simulation.py          # Real index impact testing
├── artifacts/
│   ├── postgres/plans/                   # PostgreSQL query plans
│   ├── mysql/plans/                      # MySQL query plans
│   └── unused_indexes_analysis.json      # Unused index analysis results
└── tests/                                # Test files
```

## Analysis Types

### 1. Missing Index Detection
**Rule ID**: `MISSING_INDEX_001`
- **Trigger**: Sequential scan on table with WHERE clause
- **Recommendation**: Create index on filtered columns
- **Confidence**: High (0.7-1.0)
- **Impact**: High (eliminates full table scan)

### 2. Unused Index Detection
**Rule ID**: `UNUSED_INDEX_001`
- **Trigger**: Index with zero scan count
- **Recommendation**: Drop unused index
- **Confidence**: Medium (0.3-0.7)
- **Impact**: Medium (saves space, improves writes)

### 3. Inefficient Sort Detection
**Rule ID**: `INEFFICIENT_SORT_001`
- **Trigger**: External merge sort operation
- **Recommendation**: Create index on sort columns
- **Confidence**: High (0.8-1.0)
- **Impact**: High (eliminates disk sort)

### 4. Statistics Issues
**Rule ID**: `MISSING_STATS_001`
- **Trigger**: Significant row count estimation error (>50%)
- **Recommendation**: Run ANALYZE to update statistics
- **Confidence**: Medium (0.5-0.8)
- **Impact**: Medium (improves query planning)

## Example Output

```
================================================================================
COMPREHENSIVE DATABASE ANALYSIS REPORT
================================================================================

QUERY:
  SELECT * FROM orders WHERE customer_id = 42;

SQL FEATURES:
  where_columns: ['customer_id']
  query_type: SELECT
  table_name: orders

QUERY PLAN:
  Node Type: Seq Scan
  Relation Name: orders
  Total Cost: 1887.0
  Plan Rows: 98
  Actual Rows: 99
  Rows Removed by Filter: 99901

UNUSED INDEXES:
  1. orders_pkey on orders (postgresql)
     Times used: 0
     Size: 2208 kB

RECOMMENDATIONS:
  1. MISSING_INDEX (HIGH severity)
     Rule ID: MISSING_INDEX_001
     Rationale: Sequential scan on 'orders' with WHERE clause on customer_id
     Suggested Action: CREATE INDEX idx_orders_customer_id ON orders (customer_id);
     Confidence Score: 1.0
     Impact Tier: High

  2. UNUSED_INDEX_CANDIDATE (MEDIUM severity)
     Rule ID: UNUSED_INDEX_001
     Rationale: Index 'orders_pkey' has been used 0 times
     Suggested Action: DROP INDEX orders_pkey ON orders;
     Confidence Score: 0.3
     Impact Tier: High

SUMMARY:
  Total Recommendations: 2
  Unused Indexes: 1
  High Severity: 1
  Medium Severity: 1
```

## Advanced Features

### Hypothetical Index Analysis
The tool includes simulation capabilities for testing index impact without modifying the database:
- **HypoPG Simulation**: Tests hypothetical indexes in PostgreSQL
- **Real Index Testing**: Creates temporary indexes to measure actual impact
- **Cost Comparison**: Compares before/after execution plans

### Confidence and Impact Scoring
Each recommendation includes:
- **Confidence Score**: How certain the tool is about the recommendation
- **Impact Tier**: Expected performance improvement level
- **Evidence**: Supporting data from query plans and statistics

### Multi-Database Support
- **PostgreSQL**: Full support with pg_stat_statements integration
- **MySQL**: Support with sys schema integration
- **Cross-Database**: Can analyze both databases simultaneously

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **Docker Connection Issues**
   - Ensure Docker is running
   - Check container status: `docker ps`
   - Restart containers: `docker-compose restart`

2. **Import Errors**
   - Ensure you're running from the project root directory
   - Check Python path configuration

3. **Database Connection Issues**
   - Verify containers are running and accessible
   - Check connection strings in configuration files

4. **Permission Issues**
   - Ensure proper file permissions for artifacts directory
   - Check database user permissions

### Getting Help

- Check the logs in `artifacts/` directory
- Review error messages for specific guidance
- Ensure all dependencies are properly installed
