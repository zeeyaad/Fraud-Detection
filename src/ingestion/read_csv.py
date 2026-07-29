from pathlib import Path
import pandas as pd
from typing import Optional, Union

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "data" / "raw" / "creditcard.csv"

def read_csv(filepath: Union[str, Path, None] = None) -> pd.DataFrame:
    if filepath is None:
        filepath = DEFAULT_CSV
    return pd.read_csv(filepath)