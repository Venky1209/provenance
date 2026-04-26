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

# Selected for a diverse spread of non-medical generic topics:
#   - Blog 1: MIT Tech Review (high trust tech publisher)
#   - Blog 2: The Verge (mainstream tech news)
#   - Blog 3: Medium / Towards Data Science (community/expert blog)
#   - YouTube 1: 3Blue1Brown (highly credible educational channel)
#   - YouTube 2: Marques Brownlee (mainstream tech reviewer)
#   - PubMed 1: Foundational CRISPR paper (Doudna/Charpentier 2012)

SOURCES = {
    "blogs": [
        "https://lilianweng.github.io/posts/2023-06-23-agent/",
        "https://bair.berkeley.edu/blog/2023/04/03/koala/",
        "https://huggingface.co/blog/llm-leaderboard",
    ],
    "youtube": [
        "https://www.youtube.com/watch?v=aircAruvnKk", # 3Blue1Brown - What is a Neural Network?
        "https://www.youtube.com/watch?v=jZ952vChhuI", # MKBHD - Auto Focus explanation
    ],
    "pubmed": [
        "https://pubmed.ncbi.nlm.nih.gov/22810696/", # A programmable dual-RNA-guided DNA endonuclease in adaptive bacterial immunity
    ],
}

# ── Paths ─────────────────────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(_BASE, "output")
SAMPLE_OUTPUT_PATH = os.path.join(OUTPUT_DIR, "scraped_data.json")
SUMMARY_PATH = os.path.join(OUTPUT_DIR, "summary.json")

# Assignment-required separate files
SCRAPED_DATA_DIR = os.path.join(_BASE, "scraped_data")
BLOGS_OUTPUT = os.path.join(SCRAPED_DATA_DIR, "blogs.json")
YOUTUBE_OUTPUT = os.path.join(SCRAPED_DATA_DIR, "youtube.json")
PUBMED_OUTPUT = os.path.join(SCRAPED_DATA_DIR, "pubmed.json")