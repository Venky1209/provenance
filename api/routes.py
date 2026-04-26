"""API route handlers for Provenance.

Static dataset endpoints (health, summary, sources) plus
the live POST /scrape endpoint.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from api.dataset import load_sample_data, load_summary, get_source_by_id, is_data_loaded
from models import ScrapeRequest, ScrapedDocument, SourceType, RiskFlag
from scraper import BlogScraper, YouTubeScraper, PubMedScraper, ScraperError
from scoring.trust_score import compute_trust_score
from utils.chunking import chunk_text
from utils.tagging import extract_tags
from utils import clean, detect_language, generate_source_id
from config import APP_VERSION

router = APIRouter()

# ── Static dataset endpoints ──────────────────────────────────────


@router.get("/health", tags=["Status"])
def health():
    """Service health check with build info."""
    return {
        "status": "ok",
        "version": APP_VERSION,
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "sample_data_loaded": is_data_loaded(),
        "author": "Venky1209",
        "source": "https://github.com/Venky1209/provenance",
    }


@router.get("/summary", tags=["Dataset"])
def summary():
    """Aggregate metrics from the pre-generated sample dataset."""
    data = load_summary()
    if not data:
        raise HTTPException(status_code=503, detail="Summary data not available")
    return data


@router.get("/sources", tags=["Dataset"])
def list_sources():
    """Return all records from the sample dataset."""
    data = load_sample_data()
    return {"count": len(data), "sources": data}


@router.get("/sources/{source_id}", tags=["Dataset"])
def get_source(source_id: str):
    """Return a single sample record by stable source_id."""
    record = get_source_by_id(source_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")
    return record


# ── Live scrape endpoint ──────────────────────────────────────────

SCRAPER_MAP = {
    SourceType.BLOG: BlogScraper(),
    SourceType.YOUTUBE: YouTubeScraper(),
    SourceType.PUBMED: PubMedScraper(),
}


@router.post("/scrape", tags=["Live Scrape"], response_model=ScrapedDocument)
def scrape_url(request: ScrapeRequest):
    """Live-scrape a URL through the full pipeline.

    Accepts a URL and source_type, runs scraping → cleaning →
    language detection → topic tagging → chunking → trust scoring,
    and returns a normalized record. Result is ephemeral (not persisted).
    """
    scraper = SCRAPER_MAP.get(request.source_type)
    if not scraper:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source_type: {request.source_type}",
        )

    # Validate URL basics
    url = request.url.strip()
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    try:
        raw = scraper.scrape(url)
    except Exception as exc:
        return JSONResponse(
            status_code=422,
            content={
                "status": "failed",
                "url": url,
                "error": str(exc)
            },
        )

    try:
        raw_text = raw.get("raw_text", "")
        cleaned = clean(raw_text)
        language = detect_language(cleaned)
        tags = extract_tags(cleaned)
        chunks = chunk_text(cleaned)

        from utils.date_parser import parse_date
        year, month = parse_date(raw.get("published_date", ""))

        score, breakdown, flags, reason = compute_trust_score(
            url=url,
            source_type=request.source_type.value,
            author=raw.get("author", ""),
            published_date=raw.get("published_date", ""),
            raw_text=cleaned,
            citations_count=raw.get("citations_count", 0),
            language=language,
        )

        # YouTube transcript flag
        if (request.source_type == SourceType.YOUTUBE
                and not raw.get("transcript_available", True)):
            if RiskFlag.TRANSCRIPT_UNAVAILABLE not in flags:
                flags.append(RiskFlag.TRANSCRIPT_UNAVAILABLE)
                breakdown.penalties.append(RiskFlag.TRANSCRIPT_UNAVAILABLE)

        return ScrapedDocument(
            source_id=generate_source_id(url),
            source_url=url,
            source_type=request.source_type,
            title=raw.get("title", ""),
            description=raw.get("description", ""),
            author=raw.get("author", ""),
            published_date=raw.get("published_date", ""),
            year=year,
            month=month,
            language=language,
            region=raw.get("region", ""),
            topic_tags=tags,
            trust_score=score,
            content_chunks=chunks,
            raw_text=cleaned[:2000],
            journal=raw.get("journal", ""),
            citations_count=raw.get("citations_count", 0),
            trust_breakdown=breakdown,
            risk_flags=flags,
            scoring_reason=reason,
        )
    except Exception as exc:
        return JSONResponse(
            status_code=422,
            content={
                "status": "failed",
                "url": url,
                "error": f"Pipeline failed: {str(exc)}"
            },
        )
