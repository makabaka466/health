from __future__ import annotations

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.database import SessionLocal, init_db  # noqa: E402
from app.features.rag.index_service import rebuild_rag_index  # noqa: E402


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        summary = rebuild_rag_index(db)
    finally:
        db.close()

    print("RAG index rebuild completed.")
    print(f"documents_total={summary['documents_total']}")
    print(f"documents_indexed={summary['documents_indexed']}")
    print(f"chunks_indexed={summary['chunks_indexed']}")


if __name__ == "__main__":
    main()
