from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
import os
import psycopg
from psycopg.rows import dict_row

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


class PostgresDatabase:

    def __init__(self):
        self.connection = psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            dbname=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "0000"),
            row_factory=dict_row,
        )
        self.connection.autocommit = False

    def insert_transaction(self, transaction: dict) -> None:
        query = """
        INSERT INTO raw_transactions (
            time,
            v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,
            v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,
            v21,v22,v23,v24,v25,v26,v27,v28,
            amount,
            is_fraud
        )
        VALUES (
            %(Time)s,
            %(V1)s,%(V2)s,%(V3)s,%(V4)s,%(V5)s,
            %(V6)s,%(V7)s,%(V8)s,%(V9)s,%(V10)s,
            %(V11)s,%(V12)s,%(V13)s,%(V14)s,%(V15)s,
            %(V16)s,%(V17)s,%(V18)s,%(V19)s,%(V20)s,
            %(V21)s,%(V22)s,%(V23)s,%(V24)s,%(V25)s,
            %(V26)s,%(V27)s,%(V28)s,
            %(Amount)s,
            %(Class)s
        );
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, transaction)
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logging.exception("Failed to insert transaction.")
            raise e

    def close(self):
        if self.connection:
            self.connection.close()