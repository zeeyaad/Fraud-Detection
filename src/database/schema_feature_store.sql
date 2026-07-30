-- SQL schema for feature_store
CREATE TABLE IF NOT EXISTS feature_store (
    id BIGSERIAL PRIMARY KEY,
    transaction_hash TEXT,
    time DOUBLE PRECISION,
    amount DOUBLE PRECISION,
    amount_log1p DOUBLE PRECISION,
    amount_category TEXT,
    transaction_hour SMALLINT,
    day_of_week SMALLINT,
    is_weekend BOOLEAN,
    rolling_amount_mean DOUBLE PRECISION,
    rolling_tx_count INTEGER,
    historical_fraud_rate DOUBLE PRECISION,
    is_fraud SMALLINT,
    created_at TIMESTAMP WITH TIME ZONE,
    processing_ts TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_feature_store_tx_hash ON feature_store(transaction_hash);
CREATE INDEX IF NOT EXISTS idx_feature_store_is_fraud ON feature_store(is_fraud);
