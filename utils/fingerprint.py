"""Document fingerprinting helpers.

Generates stable, deterministic IDs from URLs so the same source always
maps to the same source_id across runs.
"""

import hashlib


def generate_source_id(url: str) -> str:
    """Produce a stable 12-char hex fingerprint from a URL."""
    normalized = url.strip().lower().rstrip("/")
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]