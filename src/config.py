from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).resolve().parents[0]
load_dotenv(dotenv_path=ROOT_DIR.parent / ".env")


@dataclass(frozen=True)
class AppConfig:
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    kafka_topic: str = os.getenv("KAFKA_TOPIC", "transactions")
    kafka_group_id: str = os.getenv("KAFKA_GROUP_ID", "fraud-detection-group")
    kafka_auto_offset_reset: str = os.getenv("KAFKA_AUTO_OFFSET_RESET", "earliest")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "postgres")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "0000")
    batch_size: int = int(os.getenv("BATCH_SIZE", "500"))
    csv_path: Path = Path(os.getenv("CSV_PATH", ROOT_DIR.parent / "data" / "raw" / "creditcard.csv"))
    amount_low_threshold: float = float(os.getenv("AMOUNT_LOW_THRESHOLD", "10.0"))
    amount_high_threshold: float = float(os.getenv("AMOUNT_HIGH_THRESHOLD", "100.0"))
    rolling_window: int = int(os.getenv("ROLLING_WINDOW", "5"))
    model_dir: Path = Path(os.getenv("MODEL_DIR", ROOT_DIR.parent / "models"))
    model_name: str = os.getenv("MODEL_NAME", "fraud_detector")
    use_model_registry_db: bool = os.getenv("USE_MODEL_REGISTRY_DB", "false").lower() in ("1", "true", "yes")
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "false").lower() in ("1", "true", "yes")
    prometheus_port: int = int(os.getenv("PROMETHEUS_PORT", "8000"))
    drift_threshold: float = float(os.getenv("DRIFT_THRESHOLD", "0.1"))
    drift_bins: int = int(os.getenv("DRIFT_BINS", "10"))


def configure_logging() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
