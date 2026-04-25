"""Project-wide configuration for source targets and chunking defaults.

This module centralizes the initial seed URLs and chunking parameters used by
the scraping and content-processing pipeline.
"""

import os

# ── Chunk settings ────────────────────────────────────────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# ── HTTP settings ─────────────────────────────────────────────────
REQUEST_TIMEOUT = 15

# ── App settings ──────────────────────────────────────────────────
APP_TITLE = "Provenance — Content Trust Scoring API"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = (
    "Multi-source scraping pipeline with explainable trust scoring. "
    "Scrape blog posts, YouTube videos, and PubMed articles, then evaluate "
    "their reliability with a weighted, transparent scoring algorithm."
)

# ── Source URLs ───────────────────────────────────────────────────
# Selected for clear trust-score spread:
#   - Blog 1: Harvard Health (institutional, high trust)
#   - Blog 2: Healthline (mainstream publisher, mid trust)
#   - Blog 3: MindBodyGreen (commercial wellness, lower trust)
#   - YouTube 1: Kurzgesagt (credible science explainer)
#   - YouTube 2: Thomas DeLauer (creator-style health content)
#   - PubMed 1: Recent gut microbiome paper

SOURCES = {
    "blogs": [
        "https://www.health.harvard.edu/blog/gut-feelings-how-food-affects-your-mood-2018120715548",
        "https://www.healthline.com/nutrition/gut-microbiome-and-health",
        "https://www.mindbodygreen.com/articles/signs-of-an-unhealthy-gut",
    ],
    "youtube": [
        "https://www.youtube.com/watch?v=VzPD009qTN4",
        "https://www.youtube.com/watch?v=B9RruLkAUm8",
    ],
    "pubmed": [
        "https://pubmed.ncbi.nlm.nih.gov/31315227/",
    ],
}

# ── Paths ─────────────────────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(_BASE, "output")
SAMPLE_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "sample_output.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "summary.json")

# Assignment-required separate files
SCRAPED_DATA_DIR = os.path.join(_BASE, "scraped_data")
BLOGS_OUTPUT = os.path.join(SCRAPED_DATA_DIR, "blogs.json")
YOUTUBE_OUTPUT = os.path.join(SCRAPED_DATA_DIR, "youtube.json")
PUBMED_OUTPUT = os.path.join(SCRAPED_DATA_DIR, "pubmed.json")