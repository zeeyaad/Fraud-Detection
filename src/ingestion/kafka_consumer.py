import json
import logging

from kafka import KafkaConsumer

from ..config import AppConfig, configure_logging
from ..database.postgres import PostgresDatabase
from .validation import validate_record

configure_logging()
logger = logging.getLogger(__name__)
config = AppConfig()

def create_consumer(
    topic: str = config.kafka_topic,
    bootstrap_servers: str = config.kafka_bootstrap_servers,
    group_id: str = config.kafka_group_id,
) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset=config.kafka_auto_offset_reset,
        enable_auto_commit=False,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        group_id=group_id,
    )

def consume_transactions() -> None:
    consumer = create_consumer()
    database = PostgresDatabase()

    try:
        while True:
            raw_batch = consumer.poll(timeout_ms=1000, max_records=config.batch_size)
            if not raw_batch:
                continue

            records = []
            for messages in raw_batch.values():
                for message in messages:
                    record = message.value
                    valid, reason = validate_record(record)
                    if not valid:
                        logger.warning(
                            "Skipping invalid Kafka message offset=%s partition=%s: %s",
                            message.offset,
                            message.partition,
                            reason,
                        )
                        continue
                    records.append(record)

            if not records:
                continue

            try:
                database.insert_transactions(records)
                consumer.commit()
                logger.info("Committed %s records to Postgres.", len(records))
            except Exception:
                logger.exception("Failed to write batch to Postgres, leaving offsets uncommitted.")
    finally:
        database.close()
        consumer.close()


if __name__ == "__main__":
    consume_transactions()