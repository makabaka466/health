from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    encrypted_email = Column(Text, nullable=True)
    email_hash = Column(String(64), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    wallet_address = Column(String(42), unique=True, index=True, nullable=True)
    encrypted_wallet_address = Column(Text, nullable=True)
    wallet_address_hash = Column(String(64), unique=True, index=True, nullable=True)
    private_key_hash = Column(String(128), nullable=True)
    encrypted_private_key = Column(Text, nullable=True)
    encryption_public_key = Column(Text, nullable=True)
    encrypted_profile_data = Column(Text, nullable=True)
    public_profile_data = Column(Text, nullable=True)
    profile_is_public = Column(Boolean, default=False, nullable=False)
    home_ai_advice_cache = Column(Text, nullable=True)
    social_provider = Column(String(20), nullable=True, index=True)
    social_open_id = Column(String(128), nullable=True, index=True)
    encrypted_social_open_id = Column(Text, nullable=True)
    social_open_id_hash = Column(String(64), nullable=True, index=True)
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
