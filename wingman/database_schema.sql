-- Paul Wingman Verification Log Schema for TimescaleDB
-- Stores all verification results for historical analysis

-- Drop table if exists for clean setup
DROP TABLE IF EXISTS verification_logs CASCADE;

-- Main verification logs table
CREATE TABLE verification_logs (
    id SERIAL,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    PRIMARY KEY (id, timestamp),
    claim TEXT NOT NULL,
    verdict VARCHAR(20) NOT NULL CHECK (verdict IN ('TRUE', 'FALSE', 'UNCERTAIN', 'ERROR')),
    verifier_type VARCHAR(20) NOT NULL CHECK (verifier_type IN ('simple', 'enhanced', 'hybrid')),
    details JSONB,
    source VARCHAR(50) DEFAULT 'api',
    processing_time_ms INT,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    evidence_found TEXT[],
    checked_sources TEXT[],
    error_message TEXT
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('verification_logs', 'timestamp', if_not_exists => TRUE);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_verdict ON verification_logs (verdict);
CREATE INDEX IF NOT EXISTS idx_verifier_type ON verification_logs (verifier_type);
CREATE INDEX IF NOT EXISTS idx_timestamp ON verification_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_source ON verification_logs (source);
CREATE INDEX IF NOT EXISTS idx_claim_text ON verification_logs USING GIN (to_tsvector('english', claim));

-- Materialized view for hourly stats
CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_stats AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    verdict,
    verifier_type,
    COUNT(*) as count,
    AVG(processing_time_ms) as avg_processing_time,
    AVG(confidence_score) as avg_confidence
FROM verification_logs
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY hour, verdict, verifier_type
ORDER BY hour DESC;

-- Index for materialized view
CREATE INDEX IF NOT EXISTS idx_hourly_stats_hour ON hourly_stats (hour DESC);

-- Function to refresh materialized view
CREATE OR REPLACE FUNCTION refresh_hourly_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW hourly_stats;
END;
$$ LANGUAGE plpgsql;

-- Top false claims tracking table
CREATE TABLE IF NOT EXISTS false_claim_patterns (
    id SERIAL PRIMARY KEY,
    pattern TEXT UNIQUE NOT NULL,
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    occurrence_count INT DEFAULT 1,
    sample_claims TEXT[]
);

-- Function to update false claim patterns
CREATE OR REPLACE FUNCTION update_false_patterns()
RETURNS void AS $$
DECLARE
    rec RECORD;
BEGIN
    -- Find common false claims from last 24h
    FOR rec IN
        SELECT
            LOWER(TRIM(claim)) as normalized_claim,
            COUNT(*) as cnt,
            ARRAY_AGG(DISTINCT claim) as samples
        FROM verification_logs
        WHERE verdict = 'FALSE'
            AND timestamp > NOW() - INTERVAL '24 hours'
        GROUP BY normalized_claim
        HAVING COUNT(*) >= 2
    LOOP
        INSERT INTO false_claim_patterns (pattern, occurrence_count, sample_claims)
        VALUES (rec.normalized_claim, rec.cnt, rec.samples)
        ON CONFLICT (pattern) DO UPDATE
        SET
            last_seen = NOW(),
            occurrence_count = false_claim_patterns.occurrence_count + EXCLUDED.occurrence_count,
            sample_claims = array_cat(false_claim_patterns.sample_claims, EXCLUDED.sample_claims);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Performance stats table for verifiers
CREATE TABLE IF NOT EXISTS verifier_performance (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    verifier_type VARCHAR(20),
    total_verifications INT DEFAULT 0,
    true_count INT DEFAULT 0,
    false_count INT DEFAULT 0,
    uncertain_count INT DEFAULT 0,
    error_count INT DEFAULT 0,
    avg_processing_time_ms FLOAT,
    avg_confidence FLOAT,
    UNIQUE(date, verifier_type)
);

-- Function to update daily performance stats
CREATE OR REPLACE FUNCTION update_performance_stats()
RETURNS void AS $$
BEGIN
    INSERT INTO verifier_performance (
        date,
        verifier_type,
        total_verifications,
        true_count,
        false_count,
        uncertain_count,
        error_count,
        avg_processing_time_ms,
        avg_confidence
    )
    SELECT
        CURRENT_DATE,
        verifier_type,
        COUNT(*),
        SUM(CASE WHEN verdict = 'TRUE' THEN 1 ELSE 0 END),
        SUM(CASE WHEN verdict = 'FALSE' THEN 1 ELSE 0 END),
        SUM(CASE WHEN verdict = 'UNCERTAIN' THEN 1 ELSE 0 END),
        SUM(CASE WHEN verdict = 'ERROR' THEN 1 ELSE 0 END),
        AVG(processing_time_ms),
        AVG(confidence_score)
    FROM verification_logs
    WHERE DATE(timestamp) = CURRENT_DATE
    GROUP BY verifier_type
    ON CONFLICT (date, verifier_type) DO UPDATE
    SET
        total_verifications = EXCLUDED.total_verifications,
        true_count = EXCLUDED.true_count,
        false_count = EXCLUDED.false_count,
        uncertain_count = EXCLUDED.uncertain_count,
        error_count = EXCLUDED.error_count,
        avg_processing_time_ms = EXCLUDED.avg_processing_time_ms,
        avg_confidence = EXCLUDED.avg_confidence;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job for stats update (requires pg_cron extension)
-- Uncomment if pg_cron is available:
-- SELECT cron.schedule('update-wingman-stats', '*/15 * * * *', 'SELECT update_performance_stats(); SELECT update_false_patterns(); SELECT refresh_hourly_stats();');

-- Sample data insertion for testing
-- INSERT INTO verification_logs (claim, verdict, verifier_type, details, processing_time_ms, confidence_score)
-- VALUES
--     ('The Earth is flat', 'FALSE', 'simple', '{"evidence": "Scientific consensus"}', 150, 0.95),
--     ('Water boils at 100C at sea level', 'TRUE', 'enhanced', '{"evidence": "Scientific fact"}', 280, 0.99);

-- Useful queries
COMMENT ON TABLE verification_logs IS 'Main table for storing all verification results from Paul Wingman system';
COMMENT ON TABLE false_claim_patterns IS 'Tracks recurring false claims to identify misinformation patterns';
COMMENT ON TABLE verifier_performance IS 'Daily performance metrics for each verifier type';
COMMENT ON MATERIALIZED VIEW hourly_stats IS 'Pre-aggregated hourly statistics for dashboard display';