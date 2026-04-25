# What I Would Build Next (Phase 2)

While Phase 1 successfully proves that the ingestion, cleaning, and trust-scoring pipeline works cleanly end-to-end, there are clear paths to expand the system into a more autonomous agent.

## Phase 2: Dynamic Discovery Engine

The most impactful next step would be moving from a "URL Evaluation" tool to a "Topic Discovery" engine.

- **Topic-based URL discovery** via DuckDuckGo (for blogs/YouTube) and NCBI Entrez (for PubMed)
- **`POST /discover` endpoint**: Accepts `{ topic: "Probiotics", blogs: 3, youtube: 2, pubmed: 1 }`
- **Persistent append-only dataset** with a historical view
- **Async bulk pipeline** with concurrency controls

### Why it wasn't built yet (Scope Boundary)

Phase 1 focuses exclusively on proving the **ingestion and trust layer**. The core challenge of the assignment was evaluating *how* to score content and *how* to extract it cleanly across disparate source types.

Building the Discovery Engine introduces significant infrastructure complexity:
1. **Search engine rate limits** (DuckDuckGo/Google blocking IPs)
2. **Persistence race conditions** (appending to JSON files concurrently)
3. **Async error handling** across bulk requests

These challenges deserve their own dedicated iteration. Phase 1 proves the core scoring engine is robust; Phase 2 would automate feeding data into it.

## The One Concession: `POST /scrape`

While full discovery was deferred, the ability to evaluate *any* single URL dynamically was built into Phase 1 via the `POST /scrape` endpoint. 

This enables the interactive dashboard demo. It ensures the system isn't strictly hardcoded to a static dataset, but rather functions as a true, flexible pipeline capable of evaluating arbitrary content on the fly.
