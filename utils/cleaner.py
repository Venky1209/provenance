"""Content cleaning helpers.

Strips HTML tags, normalizes whitespace, removes navigation/ad artifacts,
and produces clean plaintext for downstream chunking and scoring.
"""

import re
import html as html_lib


_STRIP_TAGS_RE = re.compile(r"<[^>]+>")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")

_NOISE_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"share this article.*",
        r"subscribe to our newsletter.*",
        r"follow us on.*",
        r"advertisement",
        r"sponsored content",
        r"cookie\s*policy.*",
        r"privacy\s*policy.*",
        r"terms\s*(of|&)\s*(service|use).*",
        r"all rights reserved.*",
        r"©.*\d{4}.*",
        r"related\s*articles?.*",
        r"you may also like.*",
        r"read\s*more.*",
        r"click here.*",
        r"sign up.*free.*",
    ]
]


def strip_html(raw: str) -> str:
    """Remove HTML tags and decode entities."""
    text = _STRIP_TAGS_RE.sub(" ", raw)
    return html_lib.unescape(text)


def normalize_whitespace(text: str) -> str:
    """Collapse runs of spaces/tabs and limit consecutive newlines."""
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    return text.strip()


def remove_noise(text: str) -> str:
    """Remove common boilerplate lines (nav, ads, footer)."""
    lines = text.split("\n")
    cleaned: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue
        if any(p.search(stripped) for p in _NOISE_PATTERNS):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def clean(raw_html: str) -> str:
    """Full cleaning pipeline: strip → de-noise → normalize."""
    text = strip_html(raw_html)
    text = remove_noise(text)
    return normalize_whitespace(text)