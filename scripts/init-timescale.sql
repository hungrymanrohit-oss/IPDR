-- TimescaleDB initialization script for Network Flow Dashboard
-- This script sets up the database with TimescaleDB extensions and hypertables

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create the network_flows table (if not exists)
CREATE TABLE IF NOT EXISTS network_flows (
    id BIGSERIAL,
    flow_id VARCHAR(64) UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    src_ip INET NOT NULL,
    dst_ip INET NOT NULL,
    src_port INTEGER NOT NULL,
    dst_port INTEGER NOT NULL,
    protocol INTEGER NOT NULL,
    protocol_name VARCHAR(20),
    packets BIGINT DEFAULT 0,
    bytes BIGINT DEFAULT 0,
    duration DOUBLE PRECISION DEFAULT 0.0,
    input_interface INTEGER,
    output_interface INTEGER,
    tos INTEGER DEFAULT 0,
    tcp_flags INTEGER DEFAULT 0,
    src_country VARCHAR(2),
    src_city VARCHAR(100),
    dst_country VARCHAR(2),
    dst_city VARCHAR(100),
    src_asn INTEGER,
    dst_asn INTEGER,
    flow_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_network_flows_timestamp ON network_flows (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_network_flows_src_ip ON network_flows (src_ip);
CREATE INDEX IF NOT EXISTS idx_network_flows_dst_ip ON network_flows (dst_ip);
CREATE INDEX IF NOT EXISTS idx_network_flows_protocol ON network_flows (protocol);
CREATE INDEX IF NOT EXISTS idx_network_flows_src_dst_ip ON network_flows (src_ip, dst_ip);
CREATE INDEX IF NOT EXISTS idx_network_flows_created_at ON network_flows (created_at);
CREATE INDEX IF NOT EXISTS idx_network_flows_flow_id ON network_flows (flow_id);

-- Convert to hypertable
SELECT create_hypertable('network_flows', 'timestamp', if_not_exists => TRUE);

-- Set chunk time interval to 1 day
SELECT set_chunk_time_interval('network_flows', INTERVAL '1 day');

-- Create compression policy (compress chunks older than 7 days)
SELECT add_compression_policy('network_flows', INTERVAL '7 days');

-- Create retention policy (drop chunks older than 30 days)
SELECT add_retention_policy('network_flows', INTERVAL '30 days');

-- Create continuous aggregates for different time periods
-- 1-minute aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS flows_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', timestamp) AS bucket,
    COUNT(*) as total_flows,
    SUM(packets) as total_packets,
    SUM(bytes) as total_bytes,
    AVG(duration) as avg_duration,
    MAX((bytes * 8) / (duration * 1000000)) as max_bandwidth,
    AVG((bytes * 8) / (duration * 1000000)) as avg_bandwidth
FROM network_flows
GROUP BY bucket
WITH NO DATA;

-- 5-minute aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS flows_5m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', timestamp) AS bucket,
    COUNT(*) as total_flows,
    SUM(packets) as total_packets,
    SUM(bytes) as total_bytes,
    AVG(duration) as avg_duration,
    MAX((bytes * 8) / (duration * 1000000)) as max_bandwidth,
    AVG((bytes * 8) / (duration * 1000000)) as avg_bandwidth
FROM network_flows
GROUP BY bucket
WITH NO DATA;

-- 1-hour aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS flows_1h
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    COUNT(*) as total_flows,
    SUM(packets) as total_packets,
    SUM(bytes) as total_bytes,
    AVG(duration) as avg_duration,
    MAX((bytes * 8) / (duration * 1000000)) as max_bandwidth,
    AVG((bytes * 8) / (duration * 1000000)) as avg_bandwidth
FROM network_flows
GROUP BY bucket
WITH NO DATA;

-- 1-day aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS flows_1d
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    COUNT(*) as total_flows,
    SUM(packets) as total_packets,
    SUM(bytes) as total_bytes,
    AVG(duration) as avg_duration,
    MAX((bytes * 8) / (duration * 1000000)) as max_bandwidth,
    AVG((bytes * 8) / (duration * 1000000)) as avg_bandwidth
FROM network_flows
GROUP BY bucket
WITH NO DATA;

-- Add refresh policies for continuous aggregates
SELECT add_continuous_aggregate_policy('flows_1m',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('flows_5m',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('flows_1h',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('flows_1d',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Create indexes on continuous aggregates
CREATE INDEX IF NOT EXISTS idx_flows_1m_bucket ON flows_1m (bucket DESC);
CREATE INDEX IF NOT EXISTS idx_flows_5m_bucket ON flows_5m (bucket DESC);
CREATE INDEX IF NOT EXISTS idx_flows_1h_bucket ON flows_1h (bucket DESC);
CREATE INDEX IF NOT EXISTS idx_flows_1d_bucket ON flows_1d (bucket DESC);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Create a function to get top talkers
CREATE OR REPLACE FUNCTION get_top_talkers(
    hours_back INTEGER DEFAULT 24,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    ip_address INET,
    flows_count BIGINT,
    packets_count BIGINT,
    bytes_count BIGINT,
    bandwidth_mbps DOUBLE PRECISION,
    country VARCHAR(2),
    city VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.src_ip as ip_address,
        COUNT(*) as flows_count,
        SUM(f.packets) as packets_count,
        SUM(f.bytes) as bytes_count,
        AVG((f.bytes * 8) / (f.duration * 1000000)) as bandwidth_mbps,
        f.src_country as country,
        f.src_city as city
    FROM network_flows f
    WHERE f.timestamp >= NOW() - INTERVAL '1 hour' * hours_back
    GROUP BY f.src_ip, f.src_country, f.src_city
    ORDER BY bytes_count DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get protocol distribution
CREATE OR REPLACE FUNCTION get_protocol_distribution(
    hours_back INTEGER DEFAULT 24
)
RETURNS TABLE (
    protocol INTEGER,
    protocol_name VARCHAR(20),
    flows_count BIGINT,
    packets_count BIGINT,
    bytes_count BIGINT,
    percentage DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    WITH total_flows AS (
        SELECT COUNT(*) as total
        FROM network_flows
        WHERE timestamp >= NOW() - INTERVAL '1 hour' * hours_back
    )
    SELECT 
        f.protocol,
        f.protocol_name,
        COUNT(*) as flows_count,
        SUM(f.packets) as packets_count,
        SUM(f.bytes) as bytes_count,
        (COUNT(*)::DOUBLE PRECISION / t.total * 100) as percentage
    FROM network_flows f, total_flows t
    WHERE f.timestamp >= NOW() - INTERVAL '1 hour' * hours_back
    GROUP BY f.protocol, f.protocol_name, t.total
    ORDER BY bytes_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get bandwidth data over time
CREATE OR REPLACE FUNCTION get_bandwidth_data(
    hours_back INTEGER DEFAULT 24,
    interval_minutes INTEGER DEFAULT 5
)
RETURNS TABLE (
    bucket TIMESTAMPTZ,
    bandwidth_mbps DOUBLE PRECISION,
    packets_per_second DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        time_bucket(INTERVAL '1 minute' * interval_minutes, f.timestamp) as bucket,
        SUM((f.bytes * 8) / (f.duration * 1000000)) as bandwidth_mbps,
        SUM(f.packets) / (interval_minutes * 60.0) as packets_per_second
    FROM network_flows f
    WHERE f.timestamp >= NOW() - INTERVAL '1 hour' * hours_back
    GROUP BY bucket
    ORDER BY bucket;
END;
$$ LANGUAGE plpgsql;

-- Insert some sample data for testing (optional)
-- This can be removed in production
INSERT INTO network_flows (
    flow_id, timestamp, first_seen, last_seen,
    src_ip, dst_ip, src_port, dst_port, protocol, protocol_name,
    packets, bytes, duration, src_country, dst_country
) VALUES 
(
    'sample_flow_1', NOW() - INTERVAL '1 hour', 
    NOW() - INTERVAL '1 hour', NOW() - INTERVAL '1 hour' + INTERVAL '10 seconds',
    '192.168.1.100', '8.8.8.8', 12345, 53, 17, 'UDP',
    100, 1024, 10.0, 'US', 'US'
),
(
    'sample_flow_2', NOW() - INTERVAL '30 minutes',
    NOW() - INTERVAL '30 minutes', NOW() - INTERVAL '30 minutes' + INTERVAL '5 seconds',
    '192.168.1.101', '1.1.1.1', 54321, 80, 6, 'TCP',
    50, 2048, 5.0, 'US', 'US'
)
ON CONFLICT (flow_id) DO NOTHING;