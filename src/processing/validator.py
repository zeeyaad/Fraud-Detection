from __future__ import annotations

from typing import Tuple
import pandas as pd

from ..ingestion.validation import REQUIRED_COLUMNS


def validate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Validate DataFrame rows.

    Returns (valid_df, invalid_df, errors_summary).
    """
    errors = {"missing_columns": [], "invalid_rows": 0, "duplicates": 0, "type_errors": 0}

    # Check unexpected columns
    expected = set(REQUIRED_COLUMNS)
    actual = set(df.columns.tolist())
    unexpected = sorted(list(actual - expected))
    if unexpected:
        errors["missing_columns"] = unexpected

    # Detect duplicates (exact duplicates across all columns)
    dup_mask = df.duplicated(keep="first")
    duplicates = df[dup_mask]
    errors["duplicates"] = int(dup_mask.sum())

    # Basic type checks and rules
    numeric_cols = [c for c in df.columns if c.startswith("V") or c in ("Time", "Amount")]

    invalid_idx = set(duplicates.index)

    for col in numeric_cols:
        # Non-numeric will be coerced later; here we detect non-numeric entries
        non_numeric = df[~pd.to_numeric(df[col], errors="coerce").notna()].index
        invalid_idx.update(non_numeric.tolist())

    # Fraud label
    class_bad = df[~df["Class"].isin((0, 1))].index
    invalid_idx.update(class_bad.tolist())

    # Amount/Time constraints
    amt_bad = df[pd.to_numeric(df["Amount"], errors="coerce") < 0].index
    time_bad = df[pd.to_numeric(df["Time"], errors="coerce") < 0].index
    invalid_idx.update(amt_bad.tolist())
    invalid_idx.update(time_bad.tolist())

    errors["invalid_rows"] = len(invalid_idx)

    invalid_df = df.loc[sorted(invalid_idx)] if invalid_idx else df.iloc[0:0]
    valid_df = df.drop(index=sorted(invalid_idx)) if invalid_idx else df.copy()

    return valid_df.reset_index(drop=True), invalid_df.reset_index(drop=True), errors
