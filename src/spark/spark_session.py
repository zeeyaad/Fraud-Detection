from __future__ import annotations

import logging
import os
from typing import Dict

from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)


def create_spark_session(app_name: str = "fraud_etl", configs: Dict[str, str] | None = None) -> SparkSession:
    """Create and return a configured SparkSession.

    Configs may include Spark tuning options like shuffle partitions and memory settings.
    """
    builder = SparkSession.builder.appName(app_name)

    # Basic local settings if not running in cluster
    builder = builder.master(os.getenv("SPARK_MASTER", "local[*]"))

    # Apply additional configs
    configs = configs or {}
    # sensible defaults
    defaults = {
        "spark.sql.adaptive.enabled": "true",
        "spark.sql.shuffle.partitions": os.getenv("SPARK_SHUFFLE_PARTITIONS", "200"),
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
    }
    combined = {**defaults, **configs}
    for k, v in combined.items():
        builder = builder.config(k, v)

    spark = builder.getOrCreate()
    logger.info("SparkSession created with appName=%s master=%s", app_name, spark.sparkContext.master)
    return spark
