from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def init_db() -> None:
    """Create all database tables defined by ORM models."""
    from app import models  # noqa: F401 - ensures model metadata is registered
    from app.services.auth_service import ensure_admin_user

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        ensure_admin_user(db)
    finally:
        db.close()

# 依赖注入：获取数据库会话
def get_db():
    """请求级数据库会话：进入时创建，会在请求结束后自动关闭。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
