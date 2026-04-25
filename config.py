"""Project-wide configuration for source targets and chunking defaults.

This module centralizes the initial seed URLs and chunking parameters used by
the scraping and content-processing pipeline.
"""

TARGET_URLS = {
    "blogs": [
        "https://example.com/blog-one",
        "https://example.com/blog-two",
        "https://example.com/blog-three",
    ],
    "youtube": [
        "https://www.youtube.com/watch?v=example1",
        "https://www.youtube.com/watch?v=example2",
    ],
    "pubmed": [
        "https://pubmed.ncbi.nlm.nih.gov/00000000/",
    ],
}

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50