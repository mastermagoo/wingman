-- Migration: Add watcher_alerts table for Phase 4 watcher enhancement
-- Date: 2026-02-14
-- Related: WATCHER_ENHANCEMENT_DESIGN.md

-- Create watcher alerts table
CREATE TABLE IF NOT EXISTS watcher_alerts (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    worker_id TEXT,
    severity TEXT NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    message TEXT,
    fingerprint TEXT,  -- For dedup tracking
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMP,
    acknowledged_by TEXT,
    environment TEXT NOT NULL,  -- 'test' or 'prd'
    metadata JSONB  -- Store full event details
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON watcher_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_sent_at ON watcher_alerts(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_worker ON watcher_alerts(worker_id);
CREATE INDEX IF NOT EXISTS idx_alerts_acked ON watcher_alerts(acknowledged_at) WHERE acknowledged_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_alerts_fingerprint ON watcher_alerts(fingerprint);
CREATE INDEX IF NOT EXISTS idx_alerts_environment ON watcher_alerts(environment);

-- Add comments
COMMENT ON TABLE watcher_alerts IS 'Audit trail of all watcher alerts sent (30-day retention policy)';
COMMENT ON COLUMN watcher_alerts.event_type IS 'Type of event: FALSE_CLAIM, WORKER_QUARANTINED, WORKER_RELEASED, etc.';
COMMENT ON COLUMN watcher_alerts.severity IS 'Alert severity: CRITICAL (PRD+destructive), HIGH (PRD+safe), MEDIUM (TEST), LOW (info)';
COMMENT ON COLUMN watcher_alerts.fingerprint IS 'SHA256 hash for deduplication tracking';
COMMENT ON COLUMN watcher_alerts.metadata IS 'Full event details from audit log';

-- Note: Retention cleanup to be implemented via cron or scheduled task
-- Example cleanup query (run daily):
-- DELETE FROM watcher_alerts WHERE sent_at < NOW() - INTERVAL '30 days';
