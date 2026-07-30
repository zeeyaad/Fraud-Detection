from __future__ import annotations

import logging
import os
from typing import Dict

from pyspark.sql import DataFrame

from .spark_session import create_spark_session
from .transformations import (
    cast_numeric,
    remove_duplicates,
    handle_nulls,
    validate_labels,
    normalize_columns,
    add_basic_features,
    add_rolling_features,
    compute_transaction_hash,
)
from .writer import write_df_to_postgres

logger = logging.getLogger(__name__)


def _jdbc_properties() -> Dict[str, str]:
    from ..config import AppConfig

    cfg = AppConfig()
    return {
        "user": cfg.postgres_user,
        "password": cfg.postgres_password,
        "driver": "org.postgresql.Driver",
    }


def _jdbc_url() -> str:
    from ..config import AppConfig

    cfg = AppConfig()
    return f"jdbc:postgresql://{cfg.postgres_host}:{cfg.postgres_port}/{cfg.postgres_db}"


def read_raw_transactions(spark, table: str = "raw_transactions") -> DataFrame:
    props = _jdbc_properties()
    url = _jdbc_url()
    logger.info("Reading raw transactions from %s", table)
    df = spark.read.jdbc(url=url, table=table, properties=props)
    logger.info("Read %s rows from %s", df.count(), table)
    return df


def process(etl_batch: int | None = None) -> None:
    try:
        spark = create_spark_session(app_name="fraud-spark-etl")

        df = read_raw_transactions(spark)

        # Basic pipeline
        df = normalize_columns(df)
        df = cast_numeric(df)
        df = remove_duplicates(df)
        df = handle_nulls(df)
        df = validate_labels(df)

        # Cache after heavy transformations
        df = df.cache()
        df.count()  # materialize cache

        # Add features
        df = add_basic_features(df)
        df = add_rolling_features(df)
        df = compute_transaction_hash(df)

        # Explain plan for debugging/optimization
        logger.info("Execution plan:\n%s", df._jdf.queryExecution().toString())

        # Write to processed_transactions using transaction_hash uniqueness in DB
        url = _jdbc_url()
        props = _jdbc_properties()
        write_df_to_postgres(df, table="processed_transactions", jdbc_url=url, properties=props, mode="append")

    except Exception as exc:
        logger.exception("Spark ETL failed: %s", exc)
        raise


if __name__ == "__main__":
    import logging as _logging

    _logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    process()
