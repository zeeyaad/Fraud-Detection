from __future__ import annotations

import logging
from typing import Iterable

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

logger = logging.getLogger(__name__)


NUMERIC_COLUMNS = [f"V{i}" for i in range(1, 29)] + ["Time", "Amount"]


def cast_numeric(df: DataFrame, cols: Iterable[str] = NUMERIC_COLUMNS) -> DataFrame:
    for col in cols:
        if col in df.columns:
            df = df.withColumn(col, F.col(col).cast("double"))
    return df


def remove_duplicates(df: DataFrame, subset: Iterable[str] | None = None) -> DataFrame:
    if subset:
        return df.dropDuplicates(subset)
    return df.dropDuplicates()


def handle_nulls(df: DataFrame, cols: Iterable[str] | None = None) -> DataFrame:
    cols = cols or df.columns
    # For numeric columns, fill with 0; for others, fill with empty string
    numeric = set(NUMERIC_COLUMNS)
    fill_map = {c: 0 for c in cols if c in numeric and c in df.columns}
    fill_map.update({c: "" for c in cols if c not in numeric and c in df.columns})
    return df.fillna(fill_map)


def validate_labels(df: DataFrame, label_col: str = "Class") -> DataFrame:
    if label_col in df.columns:
        return df.filter(F.col(label_col).isin(0, 1))
    return df


def normalize_columns(df: DataFrame) -> DataFrame:
    # Lowercase column names
    for c in df.columns:
        df = df.withColumnRenamed(c, c.strip())
    return df


def add_basic_features(df: DataFrame, amount_low: float = 10.0, amount_high: float = 100.0) -> DataFrame:
    df = df.withColumn("processing_ts", F.current_timestamp())
    if "created_at" in df.columns:
        df = df.withColumn("created_at", F.to_timestamp(F.col("created_at")))
        df = df.withColumn("transaction_hour", F.hour(F.col("created_at")))
        df = df.withColumn("day_of_week", F.dayofweek(F.col("created_at")) - 1)
        df = df.withColumn("is_weekend", (F.col("day_of_week") >= 5))
    else:
        df = df.withColumn("transaction_hour", F.lit(None).cast("int"))
        df = df.withColumn("day_of_week", F.lit(None).cast("int"))
        df = df.withColumn("is_weekend", F.lit(False))

    df = df.withColumn("amount_log1p", F.log1p(F.coalesce(F.col("Amount"), F.lit(0.0))))
    df = df.withColumn(
        "amount_category",
        F.when(F.col("Amount") < amount_low, F.lit("Low"))
        .when(F.col("Amount") < amount_high, F.lit("Medium"))
        .otherwise(F.lit("High")),
    )

    return df


def add_rolling_features(df: DataFrame, window_size: int = 5) -> DataFrame:
    # If user_id exists, compute per-user rolling metrics, else global
    if "user_id" in df.columns and "created_at" in df.columns:
        w = Window.partitionBy("user_id").orderBy(F.col("created_at")).rowsBetween(-window_size, -1)
        w_hist = Window.partitionBy("user_id").orderBy(F.col("created_at")).rowsBetween(Window.unboundedPreceding, -1)
        df = df.withColumn("rolling_amount_mean", F.avg("Amount").over(w))
        df = df.withColumn("rolling_tx_count", F.count("Amount").over(w))
        df = df.withColumn("historical_fraud_rate", F.avg("Class").over(w_hist))
    else:
        # global rolling using order by created_at if present
        if "created_at" in df.columns:
            w = Window.orderBy(F.col("created_at")).rowsBetween(-window_size, -1)
            w_hist = Window.orderBy(F.col("created_at")).rowsBetween(Window.unboundedPreceding, -1)
            df = df.withColumn("rolling_amount_mean", F.avg("Amount").over(w))
            df = df.withColumn("rolling_tx_count", F.count("Amount").over(w))
            df = df.withColumn("historical_fraud_rate", F.avg("Class").over(w_hist))
        else:
            df = df.withColumn("rolling_amount_mean", F.lit(None))
            df = df.withColumn("rolling_tx_count", F.lit(None))
            df = df.withColumn("historical_fraud_rate", F.lit(None))

    return df


def compute_transaction_hash(df: DataFrame, cols: Iterable[str] | None = None) -> DataFrame:
    cols = cols or ["Time"] + NUMERIC_COLUMNS + ["Amount", "Class"]
    existing = [c for c in cols if c in df.columns]
    return df.withColumn("transaction_hash", F.md5(F.concat_ws(",", *[F.coalesce(F.col(c).cast("string"), F.lit("")) for c in existing])))
