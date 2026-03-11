from sqlalchemy import create_engine, inspect, text
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


def _ensure_schema_updates() -> None:
    inspector = inspect(engine)

    if "rag_knowledge_documents" not in inspector.get_table_names():
        from app import models  # noqa: F401

        models.RagKnowledgeDocument.__table__.create(bind=engine, checkfirst=True)

    if "users" in inspector.get_table_names():
        user_columns = {col["name"] for col in inspector.get_columns("users")}
        user_alter_sql = {
            "wallet_address": "ALTER TABLE users ADD COLUMN wallet_address VARCHAR(42) NULL",
            "private_key_hash": "ALTER TABLE users ADD COLUMN private_key_hash VARCHAR(128) NULL",
            "encrypted_private_key": "ALTER TABLE users ADD COLUMN encrypted_private_key TEXT NULL",
            "encrypted_profile_data": "ALTER TABLE users ADD COLUMN encrypted_profile_data TEXT NULL",
            "public_profile_data": "ALTER TABLE users ADD COLUMN public_profile_data TEXT NULL",
            "profile_is_public": "ALTER TABLE users ADD COLUMN profile_is_public BOOLEAN NOT NULL DEFAULT 0",
            "social_provider": "ALTER TABLE users ADD COLUMN social_provider VARCHAR(20) NULL",
            "social_open_id": "ALTER TABLE users ADD COLUMN social_open_id VARCHAR(128) NULL",
            "social_nickname": "ALTER TABLE users ADD COLUMN social_nickname VARCHAR(100) NULL",
        }

        with engine.begin() as conn:
            for column, sql in user_alter_sql.items():
                if column not in user_columns:
                    conn.execute(text(sql))

    if "health_data_user" in inspector.get_table_names():
        health_columns = {col["name"] for col in inspector.get_columns("health_data_user")}
        health_alter_sql = {
            "encrypted_data_content": "ALTER TABLE health_data_user ADD COLUMN encrypted_data_content TEXT NULL",
            "encrypted_pdf_data": "ALTER TABLE health_data_user ADD COLUMN encrypted_pdf_data LONGBLOB NULL",
            "is_public": "ALTER TABLE health_data_user ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT 0",
            "onchain_data_id": "ALTER TABLE health_data_user ADD COLUMN onchain_data_id VARCHAR(66) NULL",
            "onchain_tx_hash": "ALTER TABLE health_data_user ADD COLUMN onchain_tx_hash VARCHAR(66) NULL",
        }

        with engine.begin() as conn:
            for column, sql in health_alter_sql.items():
                if column not in health_columns:
                    conn.execute(text(sql))


def init_db() -> None:
    """Create all database tables defined by ORM models."""
    from app import models  # noqa: F401 - ensures model metadata is registered
    from app.features.auth.service import ensure_admin_user

    Base.metadata.create_all(bind=engine)
    _ensure_schema_updates()

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
