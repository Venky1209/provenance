"""Shared Pydantic models for pipeline input/output and API contracts."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class SourceType(str, Enum):
    BLOG = "blog"
    YOUTUBE = "youtube"
    PUBMED = "pubmed"


class RiskFlag(str, Enum):
    MISSING_AUTHOR = "missing_author"
    MISSING_DATE = "missing_date"
    NO_CITATIONS = "no_citations"
    SEO_SPAM_PATTERN = "seo_spam_pattern"
    PROMOTIONAL_LANGUAGE = "promotional_language"
    AGGRESSIVE_HEALTH_CLAIMS = "aggressive_health_claims"
    OUTDATED_MEDICAL_CONTENT = "outdated_medical_content"
    NON_ENGLISH = "non_english"
    TRANSCRIPT_UNAVAILABLE = "transcript_unavailable"


class TrustBreakdown(BaseModel):
    author_credibility: float = Field(ge=0, le=1)
    citation_count: float = Field(ge=0, le=1)
    domain_authority: float = Field(ge=0, le=1)
    recency: float = Field(ge=0, le=1)
    medical_disclaimer_presence: float = Field(ge=0, le=1)


class ScrapeRequest(BaseModel):
    url: str
    source_type: SourceType


class ScrapedDocument(BaseModel):
    source_id: str
    source_url: str
    source_type: SourceType
    title: str = ""
    description: str = ""
    author: str = ""
    published_date: str = ""
    language: str = "en"
    region: str = ""
    topic_tags: list[str] = Field(default_factory=list)
    trust_score: float = Field(ge=0, le=1)
    content_chunks: list[str] = Field(default_factory=list)
    raw_text: str = ""
    journal: str = ""
    citations_count: int = 0
    trust_breakdown: TrustBreakdown
    risk_flags: list[RiskFlag] = Field(default_factory=list)
    scoring_reason: str = ""
    scraped_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HealthResponse(BaseModel):
    status: str = "ok"
    build_timestamp: str
    sample_data_loaded: bool


class SummaryResponse(BaseModel):
    total_sources: int
    by_source_type: dict[str, int]
    by_language: dict[str, int]
    top_tags: list[dict[str, int | str]]
    trust_ranking: list[dict[str, float | str]]


class ErrorResponse(BaseModel):
    error: str
    source_type: Optional[str] = None
    detail: Optional[str] = None
