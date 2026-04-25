# jetty-scraper

Project scaffold for a production-quality, multi-source content scraping and trust scoring pipeline.

This repository is intentionally minimal for now. It defines the package layout, core configuration, and dependency list needed for future implementation of blog, YouTube, and PubMed ingestion, plus chunking, topic tagging, and trust scoring stages.

## Current structure

- `scrapers/` for source-specific scrapers and the shared base scraper contract.
- `pipeline/` for chunking, topic tagging, and trust scoring.
- `utils/` for reusable cleaning, language detection, and fingerprint helpers.
- `output/` for generated artifacts.
- `config.py` for seed URLs and chunk settings.
- `run_all.py` as the future orchestration entry point.