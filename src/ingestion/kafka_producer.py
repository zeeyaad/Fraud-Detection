import json
import logging
from typing import Any

from kafka import KafkaProducer

from ..config import AppConfig, configure_logging
from .read_csv import read_csv
from .validation import validate_record

configure_logging()
logger = logging.getLogger(__name__)
config = AppConfig()

def normalize_value(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value


def create_producer(bootstrap_servers: str = config.kafka_bootstrap_servers) -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
        retries=5,
    )


def send_transactions(topic: str = config.kafka_topic) -> None:
    producer = create_producer()
    df = read_csv()
    records = df.to_dict(orient="records")

    logger.info("Loaded %s records from CSV.", len(records))

    sent = 0
    skipped = 0

    try:
        for index, raw_record in enumerate(records, start=1):
            record = {key: normalize_value(value) for key, value in raw_record.items()}
            valid, reason = validate_record(record)
            if not valid:
                skipped += 1
                logger.warning("Skipping invalid record %s: %s", index, reason)
                continue

            try:
                producer.send(topic, value=record).get(timeout=10)
                sent += 1
            except Exception:
                logger.exception("Failed to publish record %s", index)
                raise

            if sent % config.batch_size == 0:
                producer.flush()
                logger.info("Published %s valid records so far.", sent)

        producer.flush()
        logger.info("Finished publishing records. sent=%s skipped=%s.", sent, skipped)
    finally:
        producer.close()


if __name__ == "__main__":
    send_transactions()
