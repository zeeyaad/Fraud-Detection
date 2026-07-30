-- SQL schema for processed_transactions
CREATE TABLE IF NOT EXISTS processed_transactions (
    id BIGSERIAL PRIMARY KEY,
    time DOUBLE PRECISION NOT NULL CHECK (time >= 0),
    v1 DOUBLE PRECISION,
    v2 DOUBLE PRECISION,
    v3 DOUBLE PRECISION,
    v4 DOUBLE PRECISION,
    v5 DOUBLE PRECISION,
    v6 DOUBLE PRECISION,
    v7 DOUBLE PRECISION,
    v8 DOUBLE PRECISION,
    v9 DOUBLE PRECISION,
    v10 DOUBLE PRECISION,
    v11 DOUBLE PRECISION,
    v12 DOUBLE PRECISION,
    v13 DOUBLE PRECISION,
    v14 DOUBLE PRECISION,
    v15 DOUBLE PRECISION,
    v16 DOUBLE PRECISION,
    v17 DOUBLE PRECISION,
    v18 DOUBLE PRECISION,
    v19 DOUBLE PRECISION,
    v20 DOUBLE PRECISION,
    v21 DOUBLE PRECISION,
    v22 DOUBLE PRECISION,
    v23 DOUBLE PRECISION,
    v24 DOUBLE PRECISION,
    v25 DOUBLE PRECISION,
    v26 DOUBLE PRECISION,
    v27 DOUBLE PRECISION,
    v28 DOUBLE PRECISION,
    amount DOUBLE PRECISION NOT NULL CHECK (amount >= 0),
    is_fraud SMALLINT NOT NULL CHECK (is_fraud IN (0,1)),
    transaction_hash TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Unique index to avoid duplicates across ingestion runs (hash should be populated by ETL)
CREATE UNIQUE INDEX IF NOT EXISTS idx_processed_tx_hash ON processed_transactions(transaction_hash);

-- Index useful for querying fraud cases
CREATE INDEX IF NOT EXISTS idx_processed_is_fraud ON processed_transactions(is_fraud);
