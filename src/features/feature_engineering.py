from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

from ..config import AppConfig, configure_logging

configure_logging()
logger = logging.getLogger(__name__)
config = AppConfig()


def categorize_amount(amount: float, low: float, high: float) -> str:
    if pd.isna(amount):
        return "Unknown"
    if amount < low:
        return "Low"
    if amount < high:
        return "Medium"
    return "High"


def add_time_features(df: pd.DataFrame, time_col: str = "created_at") -> pd.DataFrame:
    df = df.copy()
    if time_col not in df.columns:
        df[time_col] = pd.to_datetime("now")
    else:
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

    df["transaction_hour"] = df[time_col].dt.hour
    df["day_of_week"] = df[time_col].dt.dayofweek
    df["is_weekend"] = df["day_of_week"] >= 5
    return df


def add_amount_features(df: pd.DataFrame, low: float, high: float) -> pd.DataFrame:
    df = df.copy()
    df["amount_log1p"] = np.log1p(df["Amount"].astype(float))
    df["amount_category"] = df["Amount"].apply(lambda x: categorize_amount(x, low, high))
    return df


def add_rolling_features(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    df = df.copy()
    # Prefer user_id; otherwise use global rolling
    if "user_id" in df.columns:
        df = df.sort_values(by=["user_id", "created_at"]) if "created_at" in df.columns else df.sort_values(by=["user_id"])

        df["rolling_amount_mean"] = (
            df.groupby("user_id")["Amount"].apply(lambda s: s.rolling(window=window, min_periods=1).mean().shift(1))
        )
        df["rolling_tx_count"] = (
            df.groupby("user_id")["Amount"].apply(lambda s: s.rolling(window=window, min_periods=1).count().shift(1))
        )
        df["historical_fraud_rate"] = (
            df.groupby("user_id")["Class"].apply(lambda s: s.expanding().mean().shift(1))
        )
    else:
        # global rolling
        df = df.sort_values(by=["created_at"]) if "created_at" in df.columns else df
        df["rolling_amount_mean"] = df["Amount"].rolling(window=window, min_periods=1).mean().shift(1)
        df["rolling_tx_count"] = df["Amount"].rolling(window=window, min_periods=1).count().shift(1)
        df["historical_fraud_rate"] = df["Class"].expanding().mean().shift(1)

    return df


def engineer_features(df: pd.DataFrame, window: Optional[int] = None) -> pd.DataFrame:
    """Run full feature engineering pipeline on DataFrame."""
    window = window or getattr(config, "rolling_window", 5)
    low = getattr(config, "amount_low_threshold", 10.0)
    high = getattr(config, "amount_high_threshold", 100.0)

    df = add_time_features(df)
    df = add_amount_features(df, low, high)
    df = add_rolling_features(df, window=window)

    df["processing_ts"] = pd.Timestamp.utcnow()
    return df


def process_from_db(batch_size: int | None = None) -> None:
    """Read `processed_transactions`, engineer features in batches, and write to feature_store."""
    from ..database.postgres import PostgresDatabase
    from .feature_store import write_features
    from .statistics import descriptive_statistics

    batch_size = batch_size or config.batch_size
    db = PostgresDatabase()
    total_processed = 0
    total_rejected = 0
    start_ts = pd.Timestamp.utcnow()

    try:
        with db.connection.cursor(name="stream_processed", row_factory=dict) as cur:
            cur.execute("SELECT * FROM processed_transactions ORDER BY id")
            while True:
                rows = cur.fetchmany(batch_size)
                if not rows:
                    break

                df = pd.DataFrame(rows)
                try:
                    stats = descriptive_statistics(df)
                    logger.info("Batch stats: %s", stats)

                    features_df = engineer_features(df)
                    write_features(features_df)
                    total_processed += len(features_df)
                except Exception:
                    logger.exception("Failed to process batch; skipping")
                    total_rejected += len(df)
    finally:
        db.close()

    elapsed = (pd.Timestamp.utcnow() - start_ts).total_seconds()
    logger.info("Feature engineering complete. processed=%s rejected=%s time_s=%.2f", total_processed, total_rejected, elapsed)


if __name__ == "__main__":
    process_from_db()
