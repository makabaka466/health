from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import exceptions as qdrant_exceptions
from qdrant_client.http import models as rest

from app.config import settings


class VectorStoreError(RuntimeError):
    """Raised when vector store requests fail."""


_COLLECTION_CACHE: dict[str, int] = {}
_CLIENT: QdrantClient | None = None


def _client() -> QdrantClient:
    global _CLIENT
    if not settings.RAG_VECTOR_ENABLED:
        raise VectorStoreError("RAG 向量检索已关闭")
    if _CLIENT is None:
        _CLIENT = QdrantClient(url=settings.RAG_VECTOR_BASE_URL, timeout=settings.RAG_VECTOR_TIMEOUT_SECONDS)
    return _CLIENT


def _wrap_error(exc: Exception) -> VectorStoreError:
    return VectorStoreError(f"Qdrant 请求失败: {exc}")


def ensure_collection(vector_size: int) -> None:
    collection = settings.RAG_VECTOR_COLLECTION
    cached_size = _COLLECTION_CACHE.get(collection)
    if cached_size == vector_size:
        return

    client = _client()
    try:
        exists = client.collection_exists(collection_name=collection)
    except Exception as exc:  # noqa: BLE001
        raise _wrap_error(exc) from exc

    if not exists:
        try:
            client.create_collection(
                collection_name=collection,
                vectors_config=rest.VectorParams(size=vector_size, distance=rest.Distance.COSINE),
            )
        except Exception as exc:  # noqa: BLE001
            raise _wrap_error(exc) from exc

    _COLLECTION_CACHE[collection] = vector_size


def upsert_points(points: list[dict]) -> None:
    if not points:
        return

    client = _client()
    try:
        client.upsert(collection_name=settings.RAG_VECTOR_COLLECTION, wait=True, points=points)
    except Exception as exc:  # noqa: BLE001
        raise _wrap_error(exc) from exc


def delete_points(point_ids: list[str]) -> None:
    if not point_ids:
        return

    client = _client()
    try:
        client.delete(
            collection_name=settings.RAG_VECTOR_COLLECTION,
            points_selector=rest.PointIdsList(points=point_ids),
            wait=True,
        )
    except Exception as exc:  # noqa: BLE001
        raise _wrap_error(exc) from exc


def search_points(query_vector: list[float], limit: int, score_threshold: float | None = None) -> list[dict]:
    if not query_vector:
        return []

    client = _client()
    query_filter = rest.Filter(
        must=[
            rest.FieldCondition(
                key="is_active",
                match=rest.MatchValue(value=True),
            )
        ]
    )

    try:
        try:
            response = client.query_points(
                collection_name=settings.RAG_VECTOR_COLLECTION,
                query=query_vector,
                limit=limit,
                with_payload=True,
                with_vectors=False,
                query_filter=query_filter,
                score_threshold=score_threshold,
            )
            points = response.points
        except (AttributeError, NotImplementedError, TypeError):
            points = client.search(
                collection_name=settings.RAG_VECTOR_COLLECTION,
                query_vector=query_vector,
                limit=limit,
                with_payload=True,
                with_vectors=False,
                query_filter=query_filter,
                score_threshold=score_threshold,
            )
    except qdrant_exceptions.UnexpectedResponse as exc:
        raise _wrap_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        raise _wrap_error(exc) from exc

    results: list[dict] = []
    for point in points:
        payload = point.payload if isinstance(point.payload, dict) else {}
        results.append(
            {
                "id": str(point.id),
                "score": float(point.score or 0.0),
                "payload": payload,
            }
        )
    return results


def get_points(point_ids: list[str], with_vectors: bool = False) -> list[dict]:
    if not point_ids:
        return []

    client = _client()
    try:
        records = client.retrieve(
            collection_name=settings.RAG_VECTOR_COLLECTION,
            ids=point_ids,
            with_payload=True,
            with_vectors=with_vectors,
        )
    except qdrant_exceptions.UnexpectedResponse as exc:
        raise _wrap_error(exc) from exc
    except Exception as exc:  # noqa: BLE001
        raise _wrap_error(exc) from exc

    results: list[dict] = []
    for record in records:
        payload = record.payload if isinstance(record.payload, dict) else {}
        vector = record.vector if with_vectors else None
        if isinstance(vector, dict):
            first_vector = next(iter(vector.values()), None)
            vector = first_vector if isinstance(first_vector, list) else []
        elif not isinstance(vector, list):
            vector = []

        results.append(
            {
                "id": str(record.id),
                "payload": payload,
                "vector": vector,
            }
        )
    return results


def delete_collection() -> None:
    collection = settings.RAG_VECTOR_COLLECTION
    client = _client()
    try:
        if client.collection_exists(collection_name=collection):
            client.delete_collection(collection_name=collection)
    except Exception as exc:  # noqa: BLE001
        raise _wrap_error(exc) from exc
    _COLLECTION_CACHE.pop(collection, None)
