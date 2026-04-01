from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class HealthDataGrant(Base):
    __tablename__ = "health_data_grants"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("health_data_user.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    grantee_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    wrapped_dek = Column(Text, nullable=False)
    can_read = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)
    remark = Column(String(255), nullable=True)
    revoked_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    record = relationship("HealthData", back_populates="grants")
