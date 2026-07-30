from __future__ import annotations

import logging
from typing import Dict

from pyspark.sql import DataFrame

logger = logging.getLogger(__name__)


def write_df_to_postgres(df: DataFrame, table: str, jdbc_url: str, properties: Dict[str, str], mode: str = "append") -> None:
    """Write a Spark DataFrame to Postgres using JDBC.

    The caller should ensure deduplication is handled (e.g., via unique index on transaction_hash).
    """
    if df.rdd.isEmpty():
        logger.info("No records to write to %s", table)
        return

    # Use repartition to reduce small file problem and optionally partition by hour
    if "transaction_hour" in df.columns:
        df = df.repartition("transaction_hour")
    else:
        df = df.repartition(10)

    logger.info("Writing %s rows to table %s", df.count(), table)
    df.write.jdbc(url=jdbc_url, table=table, mode=mode, properties=properties)
    logger.info("Write to %s complete", table)
