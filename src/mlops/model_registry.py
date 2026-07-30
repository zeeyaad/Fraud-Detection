from __future__ import annotations

import json
import logging
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import AppConfig, configure_logging
from ..database.postgres import PostgresDatabase

configure_logging()
logger = logging.getLogger(__name__)
config = AppConfig()


def _serialize_json(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


class ModelRegistry:
    def __init__(self, model_dir: Path | str | None = None, model_name: str | None = None):
        self.model_dir = Path(model_dir or config.model_dir)
        self.model_name = model_name or config.model_name
        self.model_name_dir = self.model_dir / self.model_name
        self.model_name_dir.mkdir(parents=True, exist_ok=True)

    def save_model(self, model: Any, version: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Path:
        version = version or datetime.utcnow().strftime("%Y%m%d%H%M%S")
        version_dir = self.model_name_dir / version
        version_dir.mkdir(parents=True, exist_ok=False)

        model_file = version_dir / "model.pkl"
        metadata_file = version_dir / "metadata.json"

        with model_file.open("wb") as handle:
            pickle.dump(model, handle)

        metadata = metadata or {}
        metadata_payload = {
            "model_name": self.model_name,
            "version": version,
            "created_at": datetime.utcnow().isoformat(),
            "path": str(model_file),
            "metadata": {k: _serialize_json(v) for k, v in metadata.items()},
        }

        with metadata_file.open("w", encoding="utf-8") as handle:
            json.dump(metadata_payload, handle, indent=2)

        logger.info("Saved model '%s' version=%s to %s", self.model_name, version, model_file)
        if config.use_model_registry_db:
            self._register_model_metadata(metadata_payload)

        return model_file

    def load_model(self, version: Optional[str] = None) -> Any:
        version = version or self.get_latest_version()
        if not version:
            raise FileNotFoundError(f"No saved models found for '{self.model_name}'")

        model_file = self.model_dir / self.model_name / version / "model.pkl"
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")

        with model_file.open("rb") as handle:
            return pickle.load(handle)

    def get_latest_version(self) -> Optional[str]:
        versions = sorted(
            [directory.name for directory in self.model_name_dir.iterdir() if directory.is_dir()]
        )
        return versions[-1] if versions else None

    def list_versions(self) -> List[str]:
        return sorted([directory.name for directory in self.model_name_dir.iterdir() if directory.is_dir()])

    def load_metadata(self, version: Optional[str] = None) -> Dict[str, Any]:
        version = version or self.get_latest_version()
        if not version:
            raise FileNotFoundError(f"No metadata found for '{self.model_name}'")

        metadata_file = self.model_dir / self.model_name / version / "metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"Model metadata file not found: {metadata_file}")

        with metadata_file.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def list_models(self) -> List[Dict[str, Any]]:
        metadata_list: List[Dict[str, Any]] = []
        for version in self.list_versions():
            try:
                metadata_list.append(self.load_metadata(version=version))
            except FileNotFoundError:
                logger.warning("Skipping model version without metadata: %s", version)
        return metadata_list

    def _register_model_metadata(self, metadata_payload: Dict[str, Any]) -> None:
        db = PostgresDatabase()
        try:
            db.insert_model_metadata(
                model_name=metadata_payload["model_name"],
                version=metadata_payload["version"],
                model_path=metadata_payload["path"],
                metadata=metadata_payload["metadata"],
                deployed=False,
            )
        finally:
            db.close()
