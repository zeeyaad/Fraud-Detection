from __future__ import annotations

from typing import Any

REQUIRED_COLUMNS = [
    "Time",
    "V1",
    "V2",
    "V3",
    "V4",
    "V5",
    "V6",
    "V7",
    "V8",
    "V9",
    "V10",
    "V11",
    "V12",
    "V13",
    "V14",
    "V15",
    "V16",
    "V17",
    "V18",
    "V19",
    "V20",
    "V21",
    "V22",
    "V23",
    "V24",
    "V25",
    "V26",
    "V27",
    "V28",
    "Amount",
    "Class",
]


def validate_record(record: dict[str, Any]) -> tuple[bool, str]:
    missing = [col for col in REQUIRED_COLUMNS if col not in record]
    if missing:
        return False, f"Missing required fields: {missing}"

    try:
        if float(record["Time"]) < 0:
            return False, "Time must be non-negative"
        if float(record["Amount"]) < 0:
            return False, "Amount must be non-negative"
        if int(record["Class"]) not in (0, 1):
            return False, "Class must be 0 or 1"
    except (ValueError, TypeError) as exc:
        return False, f"Type validation failed: {exc}"

    return True, ""
