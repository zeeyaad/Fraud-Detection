import json
import logging
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from kafka import KafkaConsumer
from database import PostgresDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def create_consumer(topic="transactions", bootstrap_servers="localhost:9092", group_id="fraud-detection-group") -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        group_id=group_id,
    )

def consume_transactions() -> None:
    consumer = create_consumer()
    database = PostgresDatabase()

    try:
        for message in consumer:
            transaction = message.value
            try:
                database.insert_transaction(transaction)
                consumer.commit()
            except Exception:
                logger.exception("Failed to insert transaction; keeping offset uncommitted.")
    finally:
        database.close()
        consumer.close()