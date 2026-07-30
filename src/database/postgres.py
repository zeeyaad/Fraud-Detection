from __future__ import annotations

import logging

import psycopg
from psycopg.rows import dict_row

from ..config import AppConfig

config = AppConfig()
logger = logging.getLogger(__name__)


class PostgresDatabase:

    def __init__(self):
        self.connection = psycopg.connect(
            host=config.postgres_host,
            port=config.postgres_port,
            dbname=config.postgres_db,
            user=config.postgres_user,
            password=config.postgres_password,
            row_factory=dict_row,
        )
        self.connection.autocommit = False

    def insert_transactions(self, transactions: list[dict]) -> None:
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
        )
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(query, transactions)
            self.connection.commit()
            logger.info("Inserted %s transactions into Postgres.", len(transactions))
        except Exception:
            self.connection.rollback()
            logger.exception("Failed to insert transactions into Postgres.")
            raise

    def close(self):
        if self.connection:
            self.connection.close()

    def insert_processed_transactions(self, transactions: list[dict]) -> None:
        """Insert cleaned transactions into processed_transactions.

        Computes a transaction_hash server-side to deduplicate and uses ON CONFLICT DO NOTHING.
        """
        if not transactions:
            return

        query = """
        INSERT INTO processed_transactions (
            time,
            v1,v2,v3,v4,v5,v6,v7,v8,v9,v10,
            v11,v12,v13,v14,v15,v16,v17,v18,v19,v20,
            v21,v22,v23,v24,v25,v26,v27,v28,
            amount,
            is_fraud,
            transaction_hash
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
            %(Class)s,
            md5(concat_ws(',',
                %(Time)s::text, %(V1)s::text, %(V2)s::text, %(V3)s::text, %(V4)s::text,
                %(V5)s::text, %(V6)s::text, %(V7)s::text, %(V8)s::text, %(V9)s::text,
                %(V10)s::text, %(V11)s::text, %(V12)s::text, %(V13)s::text, %(V14)s::text,
                %(V15)s::text, %(V16)s::text, %(V17)s::text, %(V18)s::text, %(V19)s::text,
                %(V20)s::text, %(V21)s::text, %(V22)s::text, %(V23)s::text, %(V24)s::text,
                %(V25)s::text, %(V26)s::text, %(V27)s::text, %(V28)s::text, %(Amount)s::text, %(Class)s::text
            ))
        )
        ON CONFLICT (transaction_hash) DO NOTHING
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(query, transactions)
            self.connection.commit()
            logger.info("Inserted %s processed transactions.", len(transactions))
        except Exception:
            self.connection.rollback()
            logger.exception("Failed to insert processed transactions.")
            raise