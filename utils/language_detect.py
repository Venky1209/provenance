"""Language detection wrapper.

Uses langdetect for primary detection with graceful fallback to 'en'
when text is too short or detection fails.
"""

from langdetect import detect, LangDetectException
from langdetect import DetectorFactory

DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    """Return ISO-639-1 language code. Falls back to 'en' on failure."""
    if not text or len(text.strip()) < 20:
        return "en"
    try:
        return detect(text)
    except LangDetectException:
        return "en"