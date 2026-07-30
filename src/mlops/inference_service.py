from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import AppConfig, configure_logging
from ..database.postgres import PostgresDatabase
from .monitoring import PredictionMetrics
from .model_registry import ModelRegistry

configure_logging()
logger = logging.getLogger(__name__)
config = AppConfig()


class InferenceService:
    def __init__(
        self,
        model_registry: Optional[ModelRegistry] = None,
        db: Optional[PostgresDatabase] = None,
        metrics: Optional[PredictionMetrics] = None,
    ):
        self.model_registry = model_registry or ModelRegistry()
        self.model = self.model_registry.load_model()
        self.model_version = self.model_registry.get_latest_version()
        self.db = db or PostgresDatabase()
        self.metrics = metrics or PredictionMetrics()

    def _prepare_input(self, features: Any) -> pd.DataFrame:
        if isinstance(features, pd.DataFrame):
            return features.copy()
        if isinstance(features, dict):
            return pd.DataFrame([features])
        return pd.DataFrame(features)

    def _predict_scores(self, X: pd.DataFrame) -> Dict[str, List[Any]]:
        prediction = self.model.predict(X)
        score: List[Any] = []
        probability: List[Any] = []

        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(X)
            probability = [list(row) for row in proba.tolist()]
            if len(proba.shape) == 2 and proba.shape[1] > 1:
                score = proba[:, 1].tolist()
            else:
                score = proba[:, 0].tolist()
        elif hasattr(self.model, "decision_function"):
            score = self.model.decision_function(X).tolist()
        else:
            score = prediction.tolist() if hasattr(prediction, "tolist") else list(prediction)

        return {
            "prediction": prediction.tolist() if hasattr(prediction, "tolist") else list(prediction),
            "score": score,
            "probability": probability,
        }

    def predict(self, features: Any, feature_columns: Optional[List[str]] = None) -> pd.DataFrame:
        df = self._prepare_input(features)
        if feature_columns:
            df = df[feature_columns].copy()

        if df.empty:
            raise ValueError("No feature rows provided for inference.")

        with self.metrics.time_request():
            results = self._predict_scores(df)
            predictions = pd.DataFrame(
                {
                    "prediction": results["prediction"],
                    "score": results["score"],
                    "probability": results["probability"],
                }
            )

        predictions["model_name"] = self.model_registry.model_name
        predictions["model_version"] = self.model_version
        predictions["predicted_at"] = pd.Timestamp.utcnow()

        if "transaction_hash" in df.columns:
            predictions["transaction_hash"] = df["transaction_hash"].astype(str)

        self._persist_predictions(df, predictions)
        return pd.concat([df.reset_index(drop=True), predictions], axis=1)

    def _persist_predictions(self, features_df: pd.DataFrame, predictions_df: pd.DataFrame) -> None:
        if not config.use_model_registry_db:
            logger.debug("Model registry database integration disabled; skipping prediction persistence.")
            return

        if predictions_df.empty:
            return

        records: List[Dict[str, Any]] = []
        for index, row in predictions_df.iterrows():
            record: Dict[str, Any] = {
                "transaction_hash": row.get("transaction_hash"),
                "model_name": row["model_name"],
                "model_version": row["model_version"],
                "prediction": int(row["prediction"]),
                "score": float(row["score"]) if row["score"] is not None else None,
                "probability": row["probability"],
                "features": features_df.iloc[index].to_dict() if index < len(features_df) else {},
            }
            records.append(record)

        try:
            self.db.insert_predictions(records)
            logger.info("Persisted %s inference records.", len(records))
        except Exception:
            logger.exception("Failed to persist inference records.")
