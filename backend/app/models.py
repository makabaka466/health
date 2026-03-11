from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
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
    wallet_address = Column(String(42), unique=True, index=True, nullable=True)
    private_key_hash = Column(String(128), nullable=True)
    encrypted_private_key = Column(Text, nullable=True)
    encrypted_profile_data = Column(Text, nullable=True)
    public_profile_data = Column(Text, nullable=True)
    profile_is_public = Column(Boolean, default=False, nullable=False)
    social_provider = Column(String(20), nullable=True, index=True)
    social_open_id = Column(String(128), nullable=True, index=True)
    social_nickname = Column(String(100), nullable=True)
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
    """健康数据表：统一存储文本健康信息与 PDF 文件。"""

    __tablename__ = "health_data_user"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    data_title = Column(String(255), nullable=True)
    data_content = Column(Text, nullable=True)
    encrypted_data_content = Column(Text, nullable=True)
    pdf_data = Column(LargeBinary, nullable=True)
    encrypted_pdf_data = Column(LargeBinary, nullable=True)
    file_type = Column(Enum("text", "pdf", name="health_data_file_type"), nullable=False, default="text", index=True)
    pdf_size = Column(Integer, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    onchain_data_id = Column(String(66), nullable=True)
    onchain_tx_hash = Column(String(66), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

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


class RagKnowledgeDocument(Base):
    """RAG 知识库文档：供 AI 问答检索增强使用。"""

    __tablename__ = "rag_knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    tags = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


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


class SystemSetting(Base):
    """系统设置表：保存管理员可配置的系统级参数。"""

    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), nullable=False, unique=True, index=True)
    setting_value = Column(Text, nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class SystemLog(Base):
    """系统日志表：记录关键管理行为，方便审计。"""

    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, default="INFO", index=True)
    module = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    operator_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
