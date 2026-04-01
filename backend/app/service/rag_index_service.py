from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.features.rag.chunking import split_text_into_chunks
from app.features.rag.embeddings import EmbeddingError, embed_text, embed_texts
from app.features.rag.vector_store import VectorStoreError, delete_collection, delete_points, ensure_collection, search_points, upsert_points


logger = logging.getLogger(__name__)


class RagIndexError(RuntimeError):
    """Raised when RAG index sync/search fails."""


@dataclass
class RagSearchHit:
    document_id: int
    title: str
    category: str
    source: str | None
    tags: list[str]
    content: str
    chunk_index: int
    score: float
    updated_at: datetime


def _parse_tags(raw_tags: str | None) -> list[str]:
    if not raw_tags:
        return []
    try:
        parsed = json.loads(raw_tags)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except (TypeError, json.JSONDecodeError):
        pass
    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


def _point_id(document_id: int, chunk_index: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"rag-doc-{document_id}-chunk-{chunk_index}"))


def _parse_datetime(raw_value: str | None, fallback: datetime | None = None) -> datetime:
    if isinstance(raw_value, str) and raw_value.strip():
        try:
            return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return fallback or datetime.utcnow()


def _delete_chunk_rows(db: Session, document_id: int) -> None:
    db.query(models.RagKnowledgeChunk).filter(models.RagKnowledgeChunk.document_id == document_id).delete(synchronize_session=False)


def sync_rag_document_index(db: Session, document: models.RagKnowledgeDocument) -> int:
    if not settings.RAG_VECTOR_ENABLED:
        return 0

    existing_chunks = (
        db.query(models.RagKnowledgeChunk)
        .filter(models.RagKnowledgeChunk.document_id == document.id)
        .order_by(models.RagKnowledgeChunk.chunk_index.asc())
        .all()
    )
    existing_point_ids = [chunk.point_id for chunk in existing_chunks]

    if not document.is_active or not (document.content or "").strip():
        if existing_point_ids:
            delete_points(existing_point_ids)
        _delete_chunk_rows(db, document.id)
        db.commit()
        return 0

    chunk_texts = split_text_into_chunks(document.content)
    if not chunk_texts:
        if existing_point_ids:
            delete_points(existing_point_ids)
        _delete_chunk_rows(db, document.id)
        db.commit()
        return 0

    try:
        embeddings = embed_texts(chunk_texts)
    except EmbeddingError as exc:
        raise RagIndexError(str(exc)) from exc

    if not embeddings:
        raise RagIndexError("未能为知识库文档生成 embedding")

    try:
        ensure_collection(len(embeddings[0]))
    except VectorStoreError as exc:
        raise RagIndexError(str(exc)) from exc

    tags = _parse_tags(document.tags)
    updated_at = (document.updated_at or document.created_at or datetime.utcnow()).isoformat()
    new_rows: list[models.RagKnowledgeChunk] = []
    points: list[dict] = []
    new_point_ids: list[str] = []

    for chunk_index, (chunk_text, vector) in enumerate(zip(chunk_texts, embeddings, strict=False)):
        point_id = _point_id(document.id, chunk_index)
        new_point_ids.append(point_id)
        points.append(
            {
                "id": point_id,
                "vector": vector,
                "payload": {
                    "document_id": document.id,
                    "title": document.title,
                    "category": document.category,
                    "source": document.source,
                    "tags": tags,
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                    "updated_at": updated_at,
                    "is_active": bool(document.is_active),
                },
            }
        )
        new_rows.append(
            models.RagKnowledgeChunk(
                document_id=document.id,
                point_id=point_id,
                chunk_index=chunk_index,
                content=chunk_text,
                char_count=len(chunk_text),
                is_active=document.is_active,
            )
        )

    try:
        upsert_points(points)
        stale_point_ids = [point_id for point_id in existing_point_ids if point_id not in set(new_point_ids)]
        if stale_point_ids:
            delete_points(stale_point_ids)
    except VectorStoreError as exc:
        raise RagIndexError(str(exc)) from exc

    _delete_chunk_rows(db, document.id)
    db.add_all(new_rows)
    db.commit()
    return len(new_rows)


def delete_rag_document_index(db: Session, document_id: int) -> None:
    existing_chunks = (
        db.query(models.RagKnowledgeChunk)
        .filter(models.RagKnowledgeChunk.document_id == document_id)
        .order_by(models.RagKnowledgeChunk.chunk_index.asc())
        .all()
    )
    existing_point_ids = [chunk.point_id for chunk in existing_chunks]
    if settings.RAG_VECTOR_ENABLED and existing_point_ids:
        try:
            delete_points(existing_point_ids)
        except VectorStoreError as exc:
            raise RagIndexError(str(exc)) from exc

    _delete_chunk_rows(db, document_id)
    db.commit()


def search_rag_knowledge(question: str, limit: int) -> list[RagSearchHit]:
    if not settings.RAG_VECTOR_ENABLED or not (question or "").strip():
        return []

    try:
        query_vector = embed_text(question)
        raw_hits = search_points(
            query_vector,
            limit=max(1, limit),
            score_threshold=settings.RAG_VECTOR_SCORE_THRESHOLD,
        )
    except (EmbeddingError, VectorStoreError) as exc:
        raise RagIndexError(str(exc)) from exc

    hits: list[RagSearchHit] = []
    for item in raw_hits:
        payload = item.get("payload") if isinstance(item, dict) else None
        if not isinstance(payload, dict):
            continue
        document_id = int(payload.get("document_id") or 0)
        if not document_id:
            continue
        tags = payload.get("tags")
        hits.append(
            RagSearchHit(
                document_id=document_id,
                title=str(payload.get("title") or ""),
                category=str(payload.get("category") or ""),
                source=str(payload.get("source") or "") or None,
                tags=[str(tag).strip() for tag in tags] if isinstance(tags, list) else [],
                content=str(payload.get("content") or ""),
                chunk_index=int(payload.get("chunk_index") or 0),
                score=float(item.get("score") or 0.0),
                updated_at=_parse_datetime(payload.get("updated_at")),
            )
        )
    return hits


def rebuild_rag_index(db: Session) -> dict:
    if settings.RAG_VECTOR_ENABLED:
        try:
            delete_collection()
        except VectorStoreError as exc:
            raise RagIndexError(str(exc)) from exc

    db.query(models.RagKnowledgeChunk).delete(synchronize_session=False)
    db.commit()

    docs = db.query(models.RagKnowledgeDocument).order_by(models.RagKnowledgeDocument.id.asc()).all()
    indexed_documents = 0
    indexed_chunks = 0

    for document in docs:
        try:
            indexed_chunks += sync_rag_document_index(db, document)
            if document.is_active and (document.content or "").strip():
                indexed_documents += 1
        except RagIndexError as exc:
            logger.warning("RAG 索引重建失败，doc_id=%s: %s", document.id, exc)

    return {
        "documents_total": len(docs),
        "documents_indexed": indexed_documents,
        "chunks_indexed": indexed_chunks,
    }
