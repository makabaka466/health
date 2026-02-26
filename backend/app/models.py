from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Role(Base):
    """身份表：定义系统中的角色类型（如 admin、user）。"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), unique=True, nullable=False, index=True)
    description = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    users = relationship("User", back_populates="role_ref")


class User(Base):
    """用户账号表：保存登录信息，并通过 role_id 关联身份表。"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    role_ref = relationship("Role", back_populates="users")
    health_records = relationship("HealthData", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    article_favorites = relationship("ArticleFavorite", back_populates="user", cascade="all, delete-orphan")
    article_reads = relationship("ArticleReadHistory", back_populates="user", cascade="all, delete-orphan")


class HealthData(Base):
    """健康数据表：记录用户体征与监测数据。"""

    __tablename__ = "health_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    blood_sugar = Column(Float, nullable=True)
    recorded_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="health_records")


class ChatMessage(Base):
    """聊天记录表：保存用户与 AI 助手的对话消息。"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_user = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="chat_messages")


class HealthArticle(Base):
    """健康知识文章表：存储科普文章内容与基础统计信息。"""

    __tablename__ = "health_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    summary = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    cover_image = Column(String(500), nullable=True)
    tags = Column(String(500), nullable=True)
    view_count = Column(Integer, default=0, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    favorites = relationship("ArticleFavorite", back_populates="article", cascade="all, delete-orphan")
    read_histories = relationship("ArticleReadHistory", back_populates="article", cascade="all, delete-orphan")


class ArticleFavorite(Base):
    """文章收藏表：记录用户收藏的健康文章。"""

    __tablename__ = "article_favorites"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_article_favorite_user_article"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("health_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="article_favorites")
    article = relationship("HealthArticle", back_populates="favorites")


class ArticleReadHistory(Base):
    """文章阅读记录表：记录用户阅读行为与最近阅读时间。"""

    __tablename__ = "article_read_histories"
    __table_args__ = (UniqueConstraint("user_id", "article_id", name="uq_article_read_user_article"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("health_articles.id", ondelete="CASCADE"), nullable=False, index=True)
    read_count = Column(Integer, default=1, nullable=False)
    last_read_at = Column(DateTime, server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="article_reads")
    article = relationship("HealthArticle", back_populates="read_histories")
