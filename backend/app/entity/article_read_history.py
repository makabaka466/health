from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ArticleReadHistory(Base):
    __tablename__ = "article_read_histories"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_article_read_user_article"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("health_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    read_count = Column(Integer, default=1, nullable=False)
    last_read_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="article_reads")
    article = relationship("HealthArticle", back_populates="read_histories")
