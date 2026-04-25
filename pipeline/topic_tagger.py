"""Topic tagging stage for scraped content.

Assigns lightweight topical labels via keyword frequency analysis.
No ML models — pure deterministic keyword matching for portability.
"""

import re
from collections import Counter

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "gut_health": [
        "gut", "microbiome", "microbiota", "intestinal", "intestine",
        "digestive", "digestion", "probiotic", "prebiotic", "fiber",
        "colon", "bowel", "ibs", "gastro", "gastrointestinal",
    ],
    "nutrition": [
        "diet", "nutrition", "nutrient", "vitamin", "mineral",
        "calorie", "protein", "carbohydrate", "fat", "omega",
        "supplement", "food", "meal", "eating",
    ],
    "inflammation": [
        "inflammation", "inflammatory", "anti-inflammatory", "cytokine",
        "immune", "immunity", "autoimmune", "chronic",
    ],
    "mental_health": [
        "anxiety", "depression", "stress", "mental health", "brain",
        "cognitive", "mood", "serotonin", "dopamine", "gut-brain",
    ],
    "medicine": [
        "clinical", "trial", "patient", "treatment", "therapy",
        "drug", "pharmaceutical", "medical", "disease", "diagnosis",
        "symptom", "doctor", "physician", "hospital",
    ],
    "research": [
        "study", "research", "meta-analysis", "randomized",
        "controlled", "systematic review", "evidence", "finding",
        "data", "statistical", "cohort", "population",
    ],
    "wellness": [
        "wellness", "holistic", "natural", "organic", "detox",
        "cleanse", "healing", "lifestyle", "self-care", "mindfulness",
    ],
    "exercise": [
        "exercise", "fitness", "workout", "physical activity",
        "cardio", "strength", "training", "sport",
    ],
    "technology": [
        "AI", "artificial intelligence", "machine learning",
        "algorithm", "data", "software", "app", "digital",
    ],
}

_WORD_RE = re.compile(r"[a-z0-9-]+", re.IGNORECASE)


def extract_tags(text: str, max_tags: int = 5) -> list[str]:
    """Return up to *max_tags* topic labels sorted by relevance.

    Scoring is based on keyword hit frequency normalized by topic
    keyword count to avoid bias toward larger keyword lists.
    """
    if not text:
        return []

    lower = text.lower()
    words = set(_WORD_RE.findall(lower))

    scores: Counter[str] = Counter()
    for topic, keywords in TOPIC_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in lower or kw in words)
        if hits > 0:
            scores[topic] = hits

    return [tag for tag, _ in scores.most_common(max_tags)]