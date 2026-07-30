
# Fraud Detection - Feature Engineering

This repository implements an ingestion and processing pipeline for a credit-card fraud dataset. The project uses Kafka for ingestion and PostgreSQL for storage. The processing layer validates and cleans raw transactions and stores them in `processed_transactions`. The features layer computes engineered features and stores them in `feature_store`.

## Architecture

- Ingestion: CSV -> Kafka producer -> Kafka topics
- Consumer: Kafka -> `raw_transactions` table in Postgres
- Processing: validation + cleaning -> `processed_transactions`
- Features: feature engineering -> `feature_store`

## Feature Engineering Workflow

1. Read batches from `processed_transactions`.
2. Generate time-based features: `transaction_hour`, `day_of_week`, `is_weekend`.
3. Generate amount features: `amount_category`, `amount_log1p`.
4. Rolling features per `user_id` when available: `rolling_amount_mean`, `rolling_tx_count`, `historical_fraud_rate`.
5. Write engineered features to `feature_store` with deduplication using `transaction_hash`.

## How to run the feature pipeline

1. Ensure Docker stack is running (Postgres, Kafka).
2. Create the `feature_store` table once:

```sql
\i src/database/schema_feature_store.sql
```

3. Run the feature engineering pipeline from the repository root:

```powershell
.venv\Scripts\Activate.ps1
.venv\Scripts\python.exe -m src.features.feature_engineering
# or use the feature writer to read processed data and write features via src.features.feature_store
```

## Verification queries

```sql
SELECT COUNT(*) FROM feature_store;
SELECT * FROM feature_store LIMIT 10;
```

## MLOps support

- Use `src/database/schema_mlops.sql` to create `model_registry` and `inference_logs` tables.
- `src/mlops/model_registry.py` manages model version storage and metadata.
- `src/mlops/inference_service.py` loads the latest model, scores feature batches, and writes inference logs.
- `src/mlops/monitoring.py` exposes Prometheus metrics for inference latency, request counts, and errors.
- `src/mlops/drift_detection.py` computes PSI-based feature drift between reference and current distributions.

## Files of interest

- `src/features/feature_engineering.py` — feature functions and orchestration
- `src/features/feature_store.py` — writes features to Postgres via `PostgresDatabase.insert_feature_store`
- `src/features/statistics.py` — descriptive statistics helpers
- `src/database/schema_feature_store.sql` — SQL schema to create `feature_store`

