"""Entry point for orchestrating the full scraping pipeline.

Runs all configured scrapers, applies cleaning → language detection →
topic tagging → chunking → trust scoring, and writes the normalized
sample dataset to output/.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import (
    TARGET_URLS, OUTPUT_DIR, SAMPLE_OUTPUT_PATH, SUMMARY_PATH,
    SCRAPED_DATA_DIR, BLOGS_OUTPUT, YOUTUBE_OUTPUT, PUBMED_OUTPUT,
)
from models import ScrapedDocument, SourceType
from scrapers import BlogScraper, YouTubeScraper, PubMedScraper, ScraperError
from pipeline import chunk_text, extract_tags, compute_trust_score
from utils import clean, detect_language, generate_source_id


SCRAPER_MAP = {
    "blogs": BlogScraper(),
    "youtube": YouTubeScraper(),
    "pubmed": PubMedScraper(),
}

SOURCE_TYPE_MAP = {
    "blogs": SourceType.BLOG,
    "youtube": SourceType.YOUTUBE,
    "pubmed": SourceType.PUBMED,
}


def process_single(url: str, source_key: str) -> ScrapedDocument | None:
    """Scrape one URL through the full pipeline. Returns None on failure."""
    scraper = SCRAPER_MAP[source_key]
    source_type = SOURCE_TYPE_MAP[source_key]

    print(f"  → Scraping: {url}")
    try:
        raw = scraper.scrape(url)
    except ScraperError as exc:
        print(f"    ✗ Scraper error: {exc}")
        return None
    except Exception as exc:
        print(f"    ✗ Unexpected error: {exc}")
        return None

    raw_text = raw.get("raw_text", "")
    cleaned = clean(raw_text)
    language = detect_language(cleaned)
    tags = extract_tags(cleaned)
    chunks = chunk_text(cleaned)

    score, breakdown, flags, reason = compute_trust_score(
        url=url,
        source_type=source_type.value,
        author=raw.get("author", ""),
        published_date=raw.get("published_date", ""),
        raw_text=cleaned,
        citations_count=raw.get("citations_count", 0),
        language=language,
    )

    # Handle transcript unavailable for YouTube
    if source_type == SourceType.YOUTUBE and not raw.get("transcript_available", True):
        from models import RiskFlag
        if RiskFlag.TRANSCRIPT_UNAVAILABLE not in flags:
            flags.append(RiskFlag.TRANSCRIPT_UNAVAILABLE)

    doc = ScrapedDocument(
        source_id=generate_source_id(url),
        source_url=url,
        source_type=source_type,
        title=raw.get("title", ""),
        description=raw.get("description", ""),
        author=raw.get("author", ""),
        published_date=raw.get("published_date", ""),
        language=language,
        region=raw.get("region", ""),
        topic_tags=tags,
        trust_score=score,
        content_chunks=chunks,
        raw_text=cleaned[:2000],  # truncate for storage
        journal=raw.get("journal", ""),
        citations_count=raw.get("citations_count", 0),
        trust_breakdown=breakdown,
        risk_flags=flags,
        scoring_reason=reason,
    )

    print(f"    ✓ {doc.title[:60]}... | trust={doc.trust_score} | tags={doc.topic_tags}")
    return doc


def generate_summary(docs: list[ScrapedDocument]) -> dict:
    """Build aggregate summary from the dataset."""
    by_type: Counter = Counter()
    by_lang: Counter = Counter()
    tag_counter: Counter = Counter()

    for d in docs:
        by_type[d.source_type.value] += 1
        by_lang[d.language] += 1
        for t in d.topic_tags:
            tag_counter[t] += 1

    trust_ranking = sorted(
        [{"source_id": d.source_id, "title": d.title[:80], "trust_score": d.trust_score}
         for d in docs],
        key=lambda x: x["trust_score"],
        reverse=True,
    )

    return {
        "total_sources": len(docs),
        "by_source_type": dict(by_type),
        "by_language": dict(by_lang),
        "top_tags": [{"tag": t, "count": c} for t, c in tag_counter.most_common(10)],
        "trust_ranking": trust_ranking,
        "generated_at": datetime.utcnow().isoformat(),
    }


def main():
    """Run the full pipeline for all configured sources."""
    print("═" * 60)
    print("  Provenance — Batch Scraping Pipeline")
    print("═" * 60)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_docs: list[ScrapedDocument] = []

    for source_key, urls in TARGET_URLS.items():
        print(f"\n[{source_key.upper()}]")
        for url in urls:
            doc = process_single(url, source_key)
            if doc:
                all_docs.append(doc)

    if not all_docs:
        print("\n✗ No sources were successfully scraped.")
        sys.exit(1)

    # Write combined sample output
    output_data = [json.loads(d.model_dump_json()) for d in all_docs]
    with open(SAMPLE_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Wrote {len(all_docs)} records → {SAMPLE_OUTPUT_PATH}")

    # Write separate per-source-type files (assignment format)
    os.makedirs(SCRAPED_DATA_DIR, exist_ok=True)
    ASSIGNMENT_FIELDS = [
        "source_url", "source_type", "author", "published_date",
        "language", "region", "topic_tags", "trust_score", "content_chunks",
    ]
    source_map = {
        "blog": ([], BLOGS_OUTPUT),
        "youtube": ([], YOUTUBE_OUTPUT),
        "pubmed": ([], PUBMED_OUTPUT),
    }
    for d in all_docs:
        record = {k: v for k, v in json.loads(d.model_dump_json()).items() if k in ASSIGNMENT_FIELDS}
        source_map[d.source_type.value][0].append(record)

    for stype, (records, path) in source_map.items():
        if records:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            print(f"✓ Wrote {len(records)} {stype} records → {path}")

    # Write summary
    summary = generate_summary(all_docs)
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"✓ Wrote summary → {SUMMARY_PATH}")

    # Print trust ranking
    print("\n── Trust Ranking ──")
    for i, entry in enumerate(summary["trust_ranking"], 1):
        print(f"  {i}. [{entry['trust_score']:.2f}] {entry['title']}")

    print("\n" + "=" * 60)
    print("  Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()