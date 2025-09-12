-- Historical Performance Data Collection Schema
-- This schema stores performance snapshots for trending analysis

-- Create the historical database
CREATE DATABASE IF NOT EXISTS performance_history;

-- Connect to the historical database
\c performance_history;

-- Table for PostgreSQL query statistics snapshots
CREATE TABLE IF NOT EXISTS query_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    database_name VARCHAR(100) NOT NULL,
    query_id BIGINT,
    query_text TEXT,
    calls BIGINT,
    total_exec_time_ms DOUBLE PRECISION,
    mean_exec_time_ms DOUBLE PRECISION,
    rows BIGINT,
    shared_blks_hit BIGINT,
    shared_blks_read BIGINT,
    shared_blks_written BIGINT,
    local_blks_hit BIGINT,
    local_blks_read BIGINT,
    local_blks_written BIGINT,
    temp_blks_read BIGINT,
    temp_blks_written BIGINT,
    blk_read_time DOUBLE PRECISION,
    blk_write_time DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for MySQL slow log summaries
CREATE TABLE IF NOT EXISTS slow_log_summary (
    summary_id SERIAL PRIMARY KEY,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    database_name VARCHAR(100) NOT NULL,
    query_fingerprint TEXT,
    query_sample TEXT,
    total_time_s DOUBLE PRECISION,
    calls BIGINT,
    avg_time_s DOUBLE PRECISION,
    min_time_s DOUBLE PRECISION,
    max_time_s DOUBLE PRECISION,
    rows_examined BIGINT,
    rows_sent BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for index usage statistics
CREATE TABLE IF NOT EXISTS index_usage_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    database_name VARCHAR(100) NOT NULL,
    database_type VARCHAR(20) NOT NULL, -- 'postgresql' or 'mysql'
    table_name VARCHAR(100) NOT NULL,
    index_name VARCHAR(100) NOT NULL,
    times_used BIGINT,
    index_size_kb BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table for query plan snapshots
CREATE TABLE IF NOT EXISTS query_plan_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    database_name VARCHAR(100) NOT NULL,
    database_type VARCHAR(20) NOT NULL,
    query_text TEXT NOT NULL,
    plan_data JSONB,
    execution_time_ms DOUBLE PRECISION,
    total_cost DOUBLE PRECISION,
    rows_returned BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_query_snapshots_captured_at ON query_snapshots(captured_at);
CREATE INDEX IF NOT EXISTS idx_query_snapshots_database ON query_snapshots(database_name);
CREATE INDEX IF NOT EXISTS idx_query_snapshots_query_id ON query_snapshots(query_id);

CREATE INDEX IF NOT EXISTS idx_slow_log_captured_at ON slow_log_summary(captured_at);
CREATE INDEX IF NOT EXISTS idx_slow_log_database ON slow_log_summary(database_name);
CREATE INDEX IF NOT EXISTS idx_slow_log_fingerprint ON slow_log_summary(query_fingerprint);

CREATE INDEX IF NOT EXISTS idx_index_usage_captured_at ON index_usage_snapshots(captured_at);
CREATE INDEX IF NOT EXISTS idx_index_usage_database ON index_usage_snapshots(database_name);
CREATE INDEX IF NOT EXISTS idx_index_usage_table ON index_usage_snapshots(table_name);

CREATE INDEX IF NOT EXISTS idx_plan_snapshots_captured_at ON query_plan_snapshots(captured_at);
CREATE INDEX IF NOT EXISTS idx_plan_snapshots_database ON query_plan_snapshots(database_name);
CREATE INDEX IF NOT EXISTS idx_plan_snapshots_query_hash ON query_plan_snapshots USING hash(query_text);

-- Create a view for trending analysis
CREATE OR REPLACE VIEW query_performance_trends AS
SELECT 
    database_name,
    query_id,
    query_text,
    DATE_TRUNC('hour', captured_at) as hour_bucket,
    COUNT(*) as snapshot_count,
    AVG(total_exec_time_ms) as avg_exec_time_ms,
    MAX(total_exec_time_ms) as max_exec_time_ms,
    MIN(total_exec_time_ms) as min_exec_time_ms,
    SUM(calls) as total_calls,
    AVG(mean_exec_time_ms) as avg_mean_exec_time_ms
FROM query_snapshots
GROUP BY database_name, query_id, query_text, hour_bucket
ORDER BY hour_bucket DESC, avg_exec_time_ms DESC;

-- Create a view for index usage trends
CREATE OR REPLACE VIEW index_usage_trends AS
SELECT 
    database_name,
    table_name,
    index_name,
    DATE_TRUNC('hour', captured_at) as hour_bucket,
    AVG(times_used) as avg_times_used,
    MAX(times_used) as max_times_used,
    MIN(times_used) as min_times_used,
    AVG(index_size_kb) as avg_index_size_kb
FROM index_usage_snapshots
GROUP BY database_name, table_name, index_name, hour_bucket
ORDER BY hour_bucket DESC, avg_times_used DESC;

-- Create a function to clean up old data (keep last 30 days)
CREATE OR REPLACE FUNCTION cleanup_old_snapshots()
RETURNS void AS $$
BEGIN
    DELETE FROM query_snapshots WHERE captured_at < NOW() - INTERVAL '30 days';
    DELETE FROM slow_log_summary WHERE captured_at < NOW() - INTERVAL '30 days';
    DELETE FROM index_usage_snapshots WHERE captured_at < NOW() - INTERVAL '30 days';
    DELETE FROM query_plan_snapshots WHERE captured_at < NOW() - INTERVAL '30 days';
    
    RAISE NOTICE 'Cleaned up snapshots older than 30 days';
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
