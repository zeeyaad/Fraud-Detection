-- SQL schema for MLOps model registry and inference logs
CREATE TABLE IF NOT EXISTS model_registry (
    id BIGSERIAL PRIMARY KEY,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    model_path TEXT NOT NULL,
    metadata JSONB,
    deployed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (model_name, version)
);

CREATE INDEX IF NOT EXISTS idx_model_registry_model_name ON model_registry(model_name);
CREATE INDEX IF NOT EXISTS idx_model_registry_deployed ON model_registry(deployed);

CREATE TABLE IF NOT EXISTS inference_logs (
    id BIGSERIAL PRIMARY KEY,
    transaction_hash TEXT,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    prediction SMALLINT,
    score DOUBLE PRECISION,
    probability JSONB,
    features JSONB,
    predicted_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inference_logs_model_name ON inference_logs(model_name);
CREATE INDEX IF NOT EXISTS idx_inference_logs_transaction_hash ON inference_logs(transaction_hash);
CREATE INDEX IF NOT EXISTS idx_inference_logs_predicted_at ON inference_logs(predicted_at);
