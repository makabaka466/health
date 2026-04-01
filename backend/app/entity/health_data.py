from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class HealthData(Base):
    __tablename__ = "health_data_user"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    data_title = Column(String(255), nullable=True)
    data_content = Column(Text, nullable=True)
    encrypted_data_content = Column(Text, nullable=True)
    pdf_data = Column(LargeBinary, nullable=True)
    encrypted_pdf_data = Column(LargeBinary, nullable=True)
    owner_encrypted_dek = Column(Text, nullable=True)
    encryption_version = Column(String(20), nullable=False, default="legacy")
    file_type = Column(String(20), nullable=False, default="text", index=True)
    file_mime_type = Column(String(100), nullable=True)
    pdf_size = Column(Integer, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    onchain_data_id = Column(String(66), nullable=True)
    onchain_tx_hash = Column(String(66), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="health_records")
    grants = relationship("HealthDataGrant", back_populates="record", cascade="all, delete-orphan")
