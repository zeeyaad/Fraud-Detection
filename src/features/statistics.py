from __future__ import annotations

from typing import Dict

import pandas as pd


def descriptive_statistics(df: pd.DataFrame) -> Dict[str, object]:
    stats = {}
    stats["total_transactions"] = int(len(df))
    stats["total_fraud"] = int(df["Class"].sum()) if "Class" in df.columns else 0
    stats["fraud_percentage"] = float((stats["total_fraud"] / stats["total_transactions"]) * 100) if stats["total_transactions"] else 0.0
    stats["avg_amount"] = float(df["Amount"].mean()) if "Amount" in df.columns else None
    stats["max_amount"] = float(df["Amount"].max()) if "Amount" in df.columns else None
    stats["min_amount"] = float(df["Amount"].min()) if "Amount" in df.columns else None
    stats["std_amount"] = float(df["Amount"].std()) if "Amount" in df.columns else None
    stats["missing_values"] = int(df.isna().sum().sum())
    stats["duplicate_count"] = int(df.duplicated().sum())
    return stats
