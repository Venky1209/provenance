"""Dataset loading helpers for the API layer.

Loads the pre-generated sample_output.json and summary.json at startup
so static endpoints are fast and predictable.
"""

from __future__ import annotations

import json
import os
from typing import Any

from config import SAMPLE_OUTPUT_PATH, SUMMARY_PATH

_cache: dict[str, Any] = {}


def load_sample_data() -> list[dict]:
    """Load sample_output.json into memory. Cached after first call."""
    if "samples" not in _cache:
        if os.path.exists(SAMPLE_OUTPUT_PATH):
            with open(SAMPLE_OUTPUT_PATH, "r", encoding="utf-8") as f:
                _cache["samples"] = json.load(f)
        else:
            _cache["samples"] = []
    return _cache["samples"]


def load_summary() -> dict:
    """Load summary.json into memory. Cached after first call."""
    if "summary" not in _cache:
        if os.path.exists(SUMMARY_PATH):
            with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
                _cache["summary"] = json.load(f)
        else:
            _cache["summary"] = {}
    return _cache["summary"]


def get_source_by_id(source_id: str) -> dict | None:
    """Find a single sample record by source_id."""
    for record in load_sample_data():
        if record.get("source_id") == source_id:
            return record
    return None


def is_data_loaded() -> bool:
    """Check if sample data exists and has records."""
    return len(load_sample_data()) > 0
