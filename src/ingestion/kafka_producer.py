import json
import logging
from kafka import KafkaProducer
from read_csv import read_csv

logger = logging.getLogger(__name__)

def create_producer(bootstrap_servers="localhost:9092") -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        acks="all",
        retries=5,
    )

def send_transactions(topic="transactions") -> None:
    producer = create_producer()
    df = read_csv()
    logger.info("Loaded %s transactions.", len(df))

    for index, row in enumerate(df.to_dict(orient="records"), start=1):
        future = producer.send(topic, value=row)
        try:
            future.get(timeout=10)
        except Exception:
            logger.exception("Failed to publish record %s", index)
            raise

        if index % 1000 == 0:
            logger.info("Published %s records...", index)

    producer.flush()
    producer.close()
    logger.info("Finished publishing %s transactions.", len(df))