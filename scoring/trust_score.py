"""Trust scoring stage for scraped content.

Computes a 0–1 trust score using a weighted formula with five factors:
  author_credibility   (0.30)
  citation_count       (0.20)
  domain_authority     (0.20)
  recency              (0.20)
  medical_disclaimer   (0.10)

Also produces risk_flags and a human-readable scoring_reason.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from models import RiskFlag, TrustBreakdown

# ── Weight table ──────────────────────────────────────────────────
WEIGHTS = {
    "author_credibility": 0.30,
    "citation_count": 0.20,
    "domain_authority": 0.20,
    "recency": 0.20,
    "disclaimer": 0.10,
}

# ── Domain authority tiers ────────────────────────────────────────
_DOMAIN_TIERS: list[tuple[list[str], float]] = [
    (["pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov", "nih.gov",
      "who.int", "cdc.gov", "cochrane.org"], 1.0),
    (["mayoclinic.org", "clevelandclinic.org", "hopkinsmedicine.org",
      "health.harvard.edu", "webmd.com", "nature.com",
      "thelancet.com", "bmj.com", "nejm.org"], 0.85),
    (["healthline.com", "medicalnewstoday.com", "verywellhealth.com",
      "everydayhealth.com"], 0.65),
    (["medium.com", "wordpress.com"], 0.35),
]

_EDU_GOV_RE = re.compile(r"\.(edu|gov|ac\.\w{2})$")

# ── Patterns for abuse detection ─────────────────────────────────
_SEO_SPAM_RE = re.compile(
    r"(buy\s+now|limited\s+offer|act\s+fast|click\s+here|free\s+trial|"
    r"order\s+now|best\s+price|guaranteed|100%\s+natural|miracle\s+cure)",
    re.IGNORECASE,
)
_PROMO_RE = re.compile(
    r"(discount|coupon|affiliate|sponsored|shop\s+now|use\s+code|"
    r"special\s+offer|promo|deal\s+of\s+the\s+day)",
    re.IGNORECASE,
)
_AGGRESSIVE_CLAIMS_RE = re.compile(
    r"(cures?\s+disease|guaranteed\s+success|secret\s+remedy|"
    r"instant\s+results|no\s+risk|100%\s+guaranteed)",
    re.IGNORECASE,
)
_DISCLAIMER_RE = re.compile(
    r"(disclaimer|for\s+informational\s+purposes\s+only|"
    r"not\s+(professional|medical|legal|financial)\s+advice|"
    r"opinions\s+expressed|does\s+not\s+constitute)",
    re.IGNORECASE,
)
_CITATION_RE = re.compile(
    r"(doi[:\s]|pmid[:\s]|https?://doi\.org|https?://pubmed|"
    r"\[\d+\]|et\s+al\.|\(\d{4}\)|references?\s*:)",
    re.IGNORECASE,
)


# ── Factor functions ──────────────────────────────────────────────

def _score_author(author: str, source_type: str) -> tuple[float, str, list[str]]:
    """Score author credibility. Returns (score, reason, flags)."""
    flags: list[str] = []

    if not author or author.strip().lower() in ("unknown", "anonymous", "n/a", ""):
        flags.append("missing_author")
        return 0.6, "Weak or missing author.", flags

    name = author.strip()
    # Multiple authors (journal-style)
    if "," in name or " and " in name.lower() or ";" in name:
        return 0.75, "Multiple named authors, suggestive of journal style.", flags

    # Institutional markers
    institutional_kw = [
        "university", "institute", "hospital", "clinic", "foundation",
        "association", "department", "journal", "ministry", "center",
        "centre", "laboratory", "lab", "organization", "society",
    ]
    if any(kw in name.lower() for kw in institutional_kw):
        return 0.95, "Institutional author detected.", flags

    # Credential markers
    credential_kw = ["md", "phd", "dr.", "dr ", "prof.", "prof "]
    if any(kw in name.lower() for kw in credential_kw):
        return 0.85, "Author credentials (MD/PhD/Dr) detected.", flags

    # Named individual without credentials
    if len(name.split()) >= 2:
        return 0.6, "Named individual without explicit credentials.", flags

    # Single-word or generic handle
    return 0.35, "Single-word or generic handle, lacking verifiable history.", flags


def _score_citations(text: str, citations_count: int) -> tuple[float, str, list[str]]:
    """Score based on visible references in text."""
    flags: list[str] = []
    matches = len(_CITATION_RE.findall(text))
    total = max(matches, citations_count)

    if total == 0:
        flags.append("no_citations")
        return 0.05, "No internal citations or references found.", flags

    # Cap at 20 to prevent stuffing
    capped = min(total, 20)
    score = min(capped / 10, 1.0)
    return score, f"Found {total} visible citations.", flags


def _score_domain(url: str, source_type: str) -> tuple[float, str]:
    """Score domain authority via tiered rubric."""
    if source_type == "pubmed":
        return 1.0, "Recognized medical repository (PubMed)."
    if source_type == "youtube":
        return 0.45, "User-generated video platform (YouTube)."

    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return 0.3, "Unable to parse publishing domain."

    host = host.lower().lstrip("www.")

    for domains, score in _DOMAIN_TIERS:
        if any(host == d or host.endswith("." + d) for d in domains):
            return score, f"Recognized authority tier for {host}."

    if _EDU_GOV_RE.search(host):
        return 0.9, "Educational or government (.edu/.gov) domain."

    return 0.3, "Uncategorized or unknown domain authority."


def _score_recency(published_date: str) -> tuple[float, str, list[str]]:
    """Score content freshness. Medical content decays faster."""
    flags: list[str] = []
    if not published_date:
        flags.append("missing_date")
        return 0.5, "Missing publication date.", flags

    try:
        # Try multiple date formats
        dt = None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ",
                     "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y", "%Y"):
            try:
                dt = datetime.strptime(published_date.strip(), fmt)
                break
            except ValueError:
                continue

        if dt is None:
            # Try extracting year
            year_match = re.search(r"(20\d{2})", published_date)
            if year_match:
                dt = datetime(int(year_match.group(1)), 6, 15)
            else:
                flags.append("missing_date")
                return 0.5, "Could not robustly parse date.", flags

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        age_days = (now - dt).days

        if age_days < 0:
            return 0.9, "Future/immediate publication.", flags
        if age_days <= 365:
            return 0.95, "Published within last year (high relevance).", flags
        if age_days <= 730:
            return 0.8, "Published within 2 years.", flags
        if age_days <= 1825:  # 5 years
            return 0.55, "Published within 5 years (moderate age).", flags
        flags.append("outdated_content")
        return 0.25, "Older than 5 years (potential decay).", flags

    except Exception:
        flags.append("missing_date")
        return 0.5, "Runtime error checking date.", flags


def _score_disclaimer(text: str) -> tuple[float, str]:
    """Small positive signal for medical disclaimer presence."""
    if _DISCLAIMER_RE.search(text):
        return 0.8, "Disclaimer present, indicating accountability."
    return 0.2, "No disclaimer found."


def _detect_abuse_flags(text: str) -> list[str]:
    """Detect manipulation patterns in content."""
    flags: list[str] = []
    if _SEO_SPAM_RE.search(text):
        flags.append("seo_spam_pattern")
    if _PROMO_RE.search(text):
        flags.append("promotional_language")
    if _AGGRESSIVE_CLAIMS_RE.search(text):
        flags.append("aggressive_claims")
    return flags


# ── Main scorer ───────────────────────────────────────────────────

def compute_trust_score(
    *,
    url: str,
    source_type: str,
    author: str,
    published_date: str,
    raw_text: str,
    citations_count: int = 0,
    language: str = "en",
) -> tuple[float, TrustBreakdown, list[RiskFlag], str]:
    """Compute weighted trust score with breakdown, flags, and reason.

    Returns
    -------
    tuple of (score, breakdown, risk_flags, scoring_reason)
    """
    all_flags: list[str] = []
    reasons: list[str] = []

    # Factor scores
    author_score, author_reason, author_flags = _score_author(author, source_type)
    all_flags.extend(author_flags)

    citation_score, citation_reason, citation_flags = _score_citations(raw_text, citations_count)
    all_flags.extend(citation_flags)

    domain_score, domain_reason = _score_domain(url, source_type)

    recency_score, recency_reason, recency_flags = _score_recency(published_date)
    all_flags.extend(recency_flags)

    disclaimer_score, disclaimer_reason = _score_disclaimer(raw_text)

    # Abuse detection
    abuse_flags = _detect_abuse_flags(raw_text)
    all_flags.extend(abuse_flags)

    # Language check
    if language and language != "en":
        all_flags.append("non_english")

    # Build breakdown
    breakdown = TrustBreakdown(
        author_credibility={"score": round(author_score, 2), "reason": author_reason},
        citation_count={"score": round(citation_score, 2), "reason": citation_reason},
        domain_authority={"score": round(domain_score, 2), "reason": domain_reason},
        recency={"score": round(recency_score, 2), "reason": recency_reason},
        disclaimer={"score": round(disclaimer_score, 2), "reason": disclaimer_reason},
    )

    # Weighted sum
    raw_score = (
        author_score * WEIGHTS["author_credibility"]
        + citation_score * WEIGHTS["citation_count"]
        + domain_score * WEIGHTS["domain_authority"]
        + recency_score * WEIGHTS["recency"]
        + disclaimer_score * WEIGHTS["disclaimer"]
    )

    # Penalty for abuse flags
    penalty = len([f for f in abuse_flags]) * 0.08
    final_score = max(0.0, min(1.0, round(raw_score - penalty, 2)))

    # Build reason
    if author_score >= 0.8:
        reasons.append("strong author credibility")
    elif author_score < 0.4:
        reasons.append("weak or missing author")

    if domain_score >= 0.8:
        reasons.append("high-authority domain")
    elif domain_score < 0.4:
        reasons.append("low-authority domain")

    if citation_score >= 0.5:
        reasons.append("citations present")
    elif "no_citations" in all_flags:
        reasons.append("no visible citations")

    if "outdated_content" in all_flags:
        reasons.append("content is outdated")
    elif recency_score >= 0.8:
        reasons.append("recent content")

    if abuse_flags:
        reasons.append(f"abuse signals detected: {', '.join(abuse_flags)}")

    scoring_reason = ". ".join(reasons) + "." if reasons else "Scored within normal parameters."

    # Convert string flags to RiskFlag enums
    valid_flags = []
    for f in all_flags:
        try:
            valid_flags.append(RiskFlag(f))
        except ValueError:
            pass

    breakdown.penalties = valid_flags

    return final_score, breakdown, valid_flags, scoring_reason