from __future__ import annotations

import logging
import time
from typing import List

import psycopg
from psycopg.rows import dict_row
import pandas as pd

from ..config import AppConfig, configure_logging
from ..database.postgres import PostgresDatabase
from .validator import validate_dataframe
from .cleaner import clean_dataframe

configure_logging()
logger = logging.getLogger(__name__)
config = AppConfig()


def _rows_to_df(rows: List[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


def process_all(batch_size: int | None = None) -> None:
    start = time.time()
    batch_size = batch_size or config.batch_size

    db = PostgresDatabase()
    processed = 0
    rejected = 0

    try:
        # Stream raw transactions using server-side cursor
        with db.connection.cursor(name="stream_raw", row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM raw_transactions")
            while True:
                rows = cur.fetchmany(batch_size)
                if not rows:
                    break

                df = _rows_to_df(rows)
                total = len(df)

                valid_df, invalid_df, errors = validate_dataframe(df)

                # Cleaning
                numeric_cols = [c for c in valid_df.columns if c.startswith("V")] + ["Time", "Amount"]
                cleaned = clean_dataframe(valid_df, required_numeric=numeric_cols, required_columns=valid_df.columns.tolist())

                # Insert cleaned into processed table
                try:
                    if not cleaned.empty:
                        db.insert_processed_transactions(cleaned.to_dict(orient="records"))
                        processed += len(cleaned)
                    rejected += len(invalid_df)
                except psycopg.errors.UniqueViolation:
                    logger.warning("Duplicate detected during insert; skipping batch")
                except Exception:
                    logger.exception("Failed to insert cleaned records; aborting batch")

                logger.info("Batch processed: total=%s cleaned=%s rejected=%s summary=%s", total, len(cleaned), len(invalid_df), errors)

    finally:
        db.close()

    elapsed = time.time() - start
    logger.info("Processing complete. processed=%s rejected=%s time_s=%.2f", processed, rejected, elapsed)


if __name__ == "__main__":
    process_all()
