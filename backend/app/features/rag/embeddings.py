from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.config import settings


class EmbeddingError(RuntimeError):
    """Raised when Ollama embedding generation fails."""


def _normalize_vector(vector: list[float] | tuple[float, ...] | None) -> list[float]:
    if not isinstance(vector, (list, tuple)) or not vector:
        raise EmbeddingError("Ollama 未返回有效 embedding 向量")
    try:
        return [float(value) for value in vector]
    except (TypeError, ValueError) as exc:
        raise EmbeddingError("Ollama embedding 向量格式无效") from exc


def _ollama_json_request(path: str, payload: dict, timeout_seconds: int) -> dict:
    request = urllib.request.Request(
        url=f"{settings.OLLAMA_BASE_URL.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore") or exc.reason
        raise EmbeddingError(f"Ollama embedding HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise EmbeddingError(f"Ollama embedding 连接失败: {exc.reason}") from exc
    except TimeoutError as exc:
        raise EmbeddingError("Ollama embedding 请求超时") from exc
    except json.JSONDecodeError as exc:
        raise EmbeddingError("Ollama embedding 返回了无法解析的 JSON") from exc

    if not isinstance(data, dict):
        raise EmbeddingError("Ollama embedding 返回格式无效")
    return data


def embed_texts(texts: list[str]) -> list[list[float]]:
    clean_texts = [str(text or "").strip() for text in texts if str(text or "").strip()]
    if not clean_texts:
        return []

    batch_error: EmbeddingError | None = None
    try:
        payload = _ollama_json_request(
            "/api/embed",
            {"model": settings.OLLAMA_EMBEDDING_MODEL, "input": clean_texts},
            settings.OLLAMA_EMBEDDING_TIMEOUT_SECONDS,
        )
        embeddings = payload.get("embeddings")
        if isinstance(embeddings, list) and len(embeddings) == len(clean_texts):
            return [_normalize_vector(vector) for vector in embeddings]
        raise EmbeddingError("Ollama /api/embed 未返回完整 embeddings")
    except EmbeddingError as exc:
        batch_error = exc

    results: list[list[float]] = []
    try:
        for text in clean_texts:
            payload = _ollama_json_request(
                "/api/embeddings",
                {"model": settings.OLLAMA_EMBEDDING_MODEL, "prompt": text},
                settings.OLLAMA_EMBEDDING_TIMEOUT_SECONDS,
            )
            results.append(_normalize_vector(payload.get("embedding")))
        return results
    except EmbeddingError as exc:
        if batch_error is not None:
            raise EmbeddingError(f"{batch_error}; 兼容回退也失败: {exc}") from exc
        raise


def embed_text(text: str) -> list[float]:
    embeddings = embed_texts([text])
    if not embeddings:
        raise EmbeddingError("空文本无法生成 embedding")
    return embeddings[0]
