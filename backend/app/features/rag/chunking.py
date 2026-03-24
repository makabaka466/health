from __future__ import annotations

import re

from app.config import settings


def normalize_rag_text(text: str) -> str:
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _find_boundary(window: str, minimum_cut: int) -> int | None:
    best: int | None = None
    for match in re.finditer(r"[\n。！？!?；;]", window):
        boundary = match.end()
        if boundary >= minimum_cut:
            best = boundary
    return best


def split_text_into_chunks(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    chunk_size = max(100, chunk_size or settings.RAG_CHUNK_SIZE)
    overlap = max(0, min(overlap or settings.RAG_CHUNK_OVERLAP, chunk_size - 1))
    normalized = normalize_rag_text(text)
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    step_back = overlap

    while start < len(normalized):
        tentative_end = min(len(normalized), start + chunk_size)
        end = tentative_end

        if tentative_end < len(normalized):
            search_window = normalized[start : min(len(normalized), tentative_end + 80)]
            minimum_cut = min(len(search_window), max(int(chunk_size * 0.65), chunk_size - 80))
            boundary = _find_boundary(search_window[: chunk_size + 80], minimum_cut)
            if boundary and boundary > 0:
                end = start + boundary

        if end <= start:
            end = tentative_end

        chunk = normalized[start:end].strip()
        if chunk and (not chunks or chunk != chunks[-1]):
            chunks.append(chunk)

        if end >= len(normalized):
            break

        start = max(start + 1, end - step_back)

    return chunks
