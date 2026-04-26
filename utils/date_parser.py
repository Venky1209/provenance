"""Date parsing utility for resilient extraction of year and month."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Optional, Tuple

def parse_date(date_str: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Safely parse published_date to extract year and month.
    Handles malformed or missing dates gracefully.
    Returns (year, month) or (None, None)
    """
    if not date_str:
        return None, None
        
    date_str = date_str.strip()
    
    # Try ISO formats (e.g. YYYY-MM-DD or YYYY-MM)
    iso_match = re.match(r"^(\d{4})-(\d{2})", date_str)
    if iso_match:
        try:
            return int(iso_match.group(1)), int(iso_match.group(2))
        except ValueError:
            pass

    # Try simple full match mapping via datetime
    for fmt in ("%Y-%m-%d", "%Y-%m", "%d %b %Y", "%b %d, %Y", "%B %d, %Y", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.year, dt.month
        except ValueError:
            continue
            
    # Fallback heuristics for year
    year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
    if year_match:
        return int(year_match.group()), None
        
    return None, None
