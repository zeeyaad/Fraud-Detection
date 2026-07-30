from __future__ import annotations

import logging
from typing import List

import pandas as pd

from ..config import AppConfig, configure_logging
from ..database.postgres import PostgresDatabase

configure_logging()
logger = logging.getLogger(__name__)
config = AppConfig()


def df_to_records(df: pd.DataFrame) -> List[dict]:
    return df.to_dict(orient="records")


def write_features(df: pd.DataFrame) -> None:
    """Write engineered features DataFrame to `feature_store` table using DB helper."""
    db = PostgresDatabase()
    try:
        records = df_to_records(df)
        if not records:
            logger.info("No feature records to write.")
            return
        db.insert_feature_store(records)
        logger.info("Wrote %s feature rows to feature_store.", len(records))
    finally:
        db.close()
