from pathlib import Path

from sqlalchemy import text

from app.database import Base, engine
import app.models  # noqa: F401


def main() -> None:
    sql_file = Path(__file__).resolve().parent / "seed_health_articles.sql"
    sql_text = sql_file.read_text(encoding="utf-8")

    with engine.begin() as conn:
        # Fix old incompatible schema from manual DDL attempts.
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        conn.execute(text("DROP TABLE IF EXISTS article_read_histories"))
        conn.execute(text("DROP TABLE IF EXISTS article_favorites"))
        conn.execute(text("DROP TABLE IF EXISTS health_articles"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    # Recreate tables from SQLAlchemy models.
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        conn.execute(text("SET NAMES utf8mb4"))
        conn.exec_driver_sql(sql_text)
        result = conn.execute(text("SELECT COUNT(*) AS total FROM health_articles"))
        total = result.scalar_one()

    print(f"Imported health articles successfully. Total rows: {total}")


if __name__ == "__main__":
    main()
