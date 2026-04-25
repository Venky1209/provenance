"""Text chunking stage for scraped content.

Splits cleaned text into overlapping word-based chunks suitable for
downstream analysis. Chunk boundaries respect word boundaries to avoid
mid-word splits.
"""

from config import CHUNK_SIZE, CHUNK_OVERLAP


def chunk_text(text: str, size: int | None = None, overlap: int | None = None) -> list[str]:
    """Split *text* into overlapping word-level chunks.

    Parameters
    ----------
    text : str
        Cleaned plaintext to split.
    size : int, optional
        Maximum words per chunk (default from config).
    overlap : int, optional
        Word overlap between consecutive chunks (default from config).

    Returns
    -------
    list[str]
        Non-empty chunks. Single-chunk texts return a one-element list.
    """
    size = size or CHUNK_SIZE
    overlap = overlap or CHUNK_OVERLAP

    words = text.split()
    if not words:
        return []
    if len(words) <= size:
        return [text.strip()]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        if end >= len(words):
            break
        start = end - overlap

    return chunks