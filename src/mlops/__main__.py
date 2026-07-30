from __future__ import annotations

import argparse
import json
import logging

from .model_registry import ModelRegistry
from .monitoring import PredictionMetrics

logging.basicConfig(level="INFO", format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="MLOps utilities for the fraud detection pipeline")
    parser.add_argument("command", choices=["list", "latest", "metadata"], help="Command to run")
    parser.add_argument("--model-name", default=None, help="Override the model name from config")
    parser.add_argument("--version", default=None, help="Model version for metadata command")
    parser.add_argument("--metrics-port", type=int, default=None, help="Start Prometheus metrics server on this port")
    args = parser.parse_args()

    registry = ModelRegistry(model_name=args.model_name)

    if args.metrics_port is not None:
        PredictionMetrics(port=args.metrics_port)
        logger.info("Prometheus metrics enabled on port %s", args.metrics_port)

    if args.command == "list":
        models = registry.list_models()
        print(json.dumps(models, indent=2))
        return

    if args.command == "latest":
        latest = registry.get_latest_version()
        print(latest or "")
        return

    if args.command == "metadata":
        metadata = registry.load_metadata(version=args.version)
        print(json.dumps(metadata, indent=2))
        return


if __name__ == "__main__":
    main()
