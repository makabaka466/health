from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class RagKnowledgeChunk(Base):
    __tablename__ = "rag_knowledge_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_rag_chunk_doc_index"),)

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("rag_knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    point_id = Column(String(80), unique=True, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    char_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    document = relationship("RagKnowledgeDocument", back_populates="chunks")
