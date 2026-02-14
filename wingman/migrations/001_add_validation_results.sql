-- Migration: Add validation_results table for enhanced validation
-- Date: 2026-02-13
-- Related: AAA_VALIDATION_ENHANCEMENT_COMPLETE_PLAN.md Phase 2

-- Create validation results table
CREATE TABLE IF NOT EXISTS validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id TEXT NOT NULL,  -- Using TEXT to match approval_store format
    decision VARCHAR(20) NOT NULL CHECK (decision IN ('AUTO_APPROVED', 'AUTO_REJECTED', 'MANUAL_REVIEW')),
    composite_score INTEGER CHECK (composite_score >= 0 AND composite_score <= 100),
    semantic_analysis JSONB,
    code_scan_results JSONB,
    dependency_analysis JSONB,
    quality_assessment JSONB,
    telegram_report TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_validation_approval ON validation_results(approval_id);
CREATE INDEX IF NOT EXISTS idx_validation_decision ON validation_results(decision);
CREATE INDEX IF NOT EXISTS idx_validation_created ON validation_results(created_at DESC);

-- Add comment
COMMENT ON TABLE validation_results IS 'Stores validation results from CompositeValidator for all approval requests';
