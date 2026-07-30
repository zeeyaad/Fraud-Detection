from __future__ import annotations

from typing import Iterable
import pandas as pd


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Lowercase and strip whitespace from column names
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df


def trim_string_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=[object]).columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def safe_convert_numeric(df: pd.DataFrame, numeric_columns: Iterable[str]) -> pd.DataFrame:
    df = df.copy()
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def drop_missing_required(df: pd.DataFrame, required_columns: Iterable[str]) -> pd.DataFrame:
    df = df.copy()
    return df.dropna(subset=list(required_columns))


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    return df.drop_duplicates(keep="first")


def clean_dataframe(df: pd.DataFrame, required_numeric: Iterable[str], required_columns: Iterable[str]) -> pd.DataFrame:
    df = normalize_columns(df)
    df = trim_string_columns(df)
    df = safe_convert_numeric(df, required_numeric)
    df = drop_missing_required(df, required_columns)
    df = remove_duplicates(df)
    return df.reset_index(drop=True)
