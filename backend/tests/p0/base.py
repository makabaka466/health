from __future__ import annotations

import os
import sys
import unittest
import uuid
import asyncio
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parent
TEST_DB_PATH = BACKEND_DIR / "tests" / ".tmp" / "p0_test.sqlite3"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RAG_VECTOR_ENABLED", "false")
os.environ.setdefault("HEALTH_DATA_CONTRACT_ADDRESS", "")
os.environ.setdefault("HEALTH_DATA_CONTRACT_ABI_JSON", "")
os.environ.setdefault("OLLAMA_DISABLE_THINKING", "true")

import httpx

from app.main import app
from app.database import Base, SessionLocal, engine
from app.features.auth.service import ensure_admin_user


class StreamResponse:
    def __init__(self, status_code: int, text: str, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self.headers = headers or {}

    def __enter__(self) -> "StreamResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def iter_text(self):
        yield self.text


class SyncASGIClient:
    def __init__(self, fastapi_app) -> None:
        self.app = fastapi_app
        self.base_url = "http://testserver"

    async def _request_async(self, method: str, url: str, **kwargs):
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url=self.base_url) as client:
            return await client.request(method, url, **kwargs)

    async def _stream_async(self, method: str, url: str, **kwargs) -> StreamResponse:
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url=self.base_url) as client:
            async with client.stream(method, url, **kwargs) as response:
                body = "".join([chunk async for chunk in response.aiter_text()])
                return StreamResponse(
                    status_code=response.status_code,
                    text=body,
                    headers=dict(response.headers),
                )

    def request(self, method: str, url: str, **kwargs):
        return asyncio.run(self._request_async(method, url, **kwargs))

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs):
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def stream(self, method: str, url: str, **kwargs) -> StreamResponse:
        return asyncio.run(self._stream_async(method, url, **kwargs))

    def close(self) -> None:
        return None


class BackendP0TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = SyncASGIClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()

    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            ensure_admin_user(db)
        finally:
            db.close()

    def db_session(self):
        return SessionLocal()

    def unique_value(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:8]}"

    def register_user(
        self,
        *,
        username: str | None = None,
        email: str | None = None,
        password: str = "Test123456!",
    ) -> dict[str, Any]:
        username = username or self.unique_value("user")
        email = email or f"{self.unique_value('mail')}@example.com"
        payload = {
            "username": username,
            "email": email,
            "password": password,
        }
        response = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        data = response.json()
        data["_raw_password"] = password
        data["_raw_email"] = email
        data["_raw_username"] = username
        return data

    def login_user(self, username: str, password: str) -> dict[str, Any]:
        response = self.client.post(
            "/api/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def login_admin(self, username: str = "admin", password: str = "admin123") -> dict[str, Any]:
        response = self.client.post(
            "/api/auth/admin/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def user_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def admin_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def minimal_pdf_base64() -> str:
        raw = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        import base64

        return "data:application/pdf;base64," + base64.b64encode(raw).decode("utf-8")
