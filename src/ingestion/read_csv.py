from pathlib import Path
from typing import Union

import pandas as pd

from ..config import AppConfig
from .validation import REQUIRED_COLUMNS

config = AppConfig()

def read_csv(filepath: Union[str, Path, None] = None) -> pd.DataFrame:
    if filepath is None:
        filepath = config.csv_path

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV file is missing required columns: {missing_columns}")

    return df


load_csv = read_csv