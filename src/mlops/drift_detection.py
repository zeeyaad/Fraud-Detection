from __future__ import annotations

import logging
from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd

from ..config import AppConfig, configure_logging

configure_logging()
logger = logging.getLogger(__name__)
config = AppConfig()


def _safe_proportions(values: np.ndarray, bins: np.ndarray) -> np.ndarray:
    counts, _ = np.histogram(values, bins=bins)
    proportions = counts.astype(float) / max(len(values), 1)
    return np.where(proportions == 0, 1e-8, proportions)


def population_stability_index(
    reference: pd.Series,
    current: pd.Series,
    buckets: int = 10,
) -> float:
    reference = reference.dropna().astype(float)
    current = current.dropna().astype(float)

    if reference.empty or current.empty:
        return 0.0

    quantiles = np.linspace(0.0, 1.0, buckets + 1)
    boundaries = np.unique(np.quantile(reference, quantiles))
    if len(boundaries) <= 1:
        return 0.0

    ref_props = _safe_proportions(reference.to_numpy(), boundaries)
    cur_props = _safe_proportions(current.to_numpy(), boundaries)

    psi = np.sum((ref_props - cur_props) * np.log(cur_props / ref_props))
    return float(np.nan_to_num(psi, nan=0.0, posinf=0.0, neginf=0.0))


class DriftDetector:
    def __init__(self, threshold: Optional[float] = None, bins: Optional[int] = None):
        self.threshold = threshold if threshold is not None else config.drift_threshold
        self.bins = bins if bins is not None else config.drift_bins

    def detect_feature_drift(
        self,
        reference: pd.DataFrame,
        current: pd.DataFrame,
        features: Optional[Iterable[str]] = None,
    ) -> Dict[str, float]:
        if features is None:
            features = [col for col in current.columns if current[col].dtype.kind in "bifc"]

        drift_scores: Dict[str, float] = {}
        for feature in features:
            if feature not in reference.columns or feature not in current.columns:
                continue
            try:
                score = population_stability_index(reference[feature], current[feature], buckets=self.bins)
                drift_scores[feature] = score
            except Exception:
                logger.exception("Failed to compute drift for feature %s", feature)
                drift_scores[feature] = 0.0

        return drift_scores

    def has_drift(self, reference: pd.DataFrame, current: pd.DataFrame, features: Optional[Iterable[str]] = None) -> bool:
        scores = self.detect_feature_drift(reference, current, features=features)
        if not scores:
            return False
        max_score = max(scores.values())
        logger.info("Drift scores: %s", scores)
        return max_score >= self.threshold
