-- ============================================
-- PostgreSQL Initialization Script (Supabase)
-- Real-Time Financial Fraud Detection Pipeline
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- RAW TRANSACTIONS TABLE
-- Stores all incoming transactions for analytics
-- ============================================
CREATE TABLE IF NOT EXISTS transactions (
    id BIGSERIAL PRIMARY KEY,
    transaction_id UUID NOT NULL,
    user_id INTEGER NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    city VARCHAR(255) NOT NULL,
    merchant_category VARCHAR(100) NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Indexes for performance
    CONSTRAINT unique_transaction UNIQUE (transaction_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_user_timestamp ON transactions(user_id, timestamp DESC);

-- Partition by month for better performance (optional)
-- Note: You may want to enable partitioning in production
-- CREATE INDEX idx_transactions_timestamp_brin ON transactions USING BRIN (timestamp);

-- ============================================
-- FRAUD ALERTS TABLE
-- Stores fraud detection results from Flink
-- ============================================
CREATE TABLE IF NOT EXISTS fraud_alerts (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    transaction_count INTEGER NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    is_fraud SMALLINT NOT NULL CHECK (is_fraud IN (0, 1)),
    alert_reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Prevent duplicate alerts for same window
    CONSTRAINT unique_alert_window UNIQUE (user_id, window_end)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_fraud_alerts_user_id ON fraud_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_fraud_alerts_window_end ON fraud_alerts(window_end DESC);
CREATE INDEX IF NOT EXISTS idx_fraud_alerts_is_fraud ON fraud_alerts(is_fraud) WHERE is_fraud = 1;

-- ============================================
-- ANALYTICS VIEWS
-- Pre-aggregated data for dashboard queries
-- ============================================

-- Transaction volume per minute (for live charts)
CREATE OR REPLACE VIEW transactions_per_minute AS
SELECT
    DATE_TRUNC('minute', timestamp) AS minute,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_volume,
    AVG(amount) AS avg_amount
FROM transactions
WHERE timestamp >= NOW() - INTERVAL '1 hour'
GROUP BY DATE_TRUNC('minute', timestamp)
ORDER BY minute DESC;

-- Fraud cases by city (last hour)
CREATE OR REPLACE VIEW fraud_by_city AS
SELECT
    t.city,
    COUNT(*) AS fraud_count,
    SUM(t.amount) AS total_fraud_amount
FROM transactions t
INNER JOIN fraud_alerts fa 
    ON t.user_id = fa.user_id
    AND t.timestamp >= fa.window_start
    AND t.timestamp < fa.window_end
WHERE fa.is_fraud = 1
    AND fa.window_end >= NOW() - INTERVAL '1 hour'
GROUP BY t.city
ORDER BY fraud_count DESC;

-- Total fraud stats (last 24 hours)
CREATE OR REPLACE VIEW fraud_stats_24h AS
SELECT
    COUNT(*) AS total_alerts,
    COUNT(*) FILTER (WHERE is_fraud = 1) AS fraud_count,
    SUM(total_amount) FILTER (WHERE is_fraud = 1) AS fraud_total_amount,
    COUNT(DISTINCT user_id) AS unique_users_flagged
FROM fraud_alerts
WHERE window_end >= NOW() - INTERVAL '24 hours';

-- ============================================
-- TABLE CLEANUP POLICIES (Optional)
-- Use pg_cron extension for automatic cleanup
-- ============================================

-- Delete old transactions (older than 30 days)
-- Requires pg_cron extension enabled in Supabase
-- SELECT cron.schedule(
--     'cleanup-old-transactions',
--     '0 2 * * *', -- Daily at 2 AM
--     $$DELETE FROM transactions WHERE timestamp < NOW() - INTERVAL '30 days'$$
-- );

-- Delete old fraud alerts (older than 30 days)
-- SELECT cron.schedule(
--     'cleanup-old-alerts',
--     '0 3 * * *', -- Daily at 3 AM
--     $$DELETE FROM fraud_alerts WHERE window_end < NOW() - INTERVAL '30 days'$$
-- );

-- ============================================
-- GRANTS (Adjust based on Supabase roles)
-- ============================================
-- Note: Supabase already handles role management
-- You may need to grant access if using custom roles

-- GRANT SELECT, INSERT ON transactions TO authenticated;
-- GRANT SELECT, INSERT ON fraud_alerts TO authenticated;
-- GRANT SELECT ON transactions_per_minute TO authenticated;
-- GRANT SELECT ON fraud_by_city TO authenticated;
-- GRANT SELECT ON fraud_stats_24h TO authenticated;
