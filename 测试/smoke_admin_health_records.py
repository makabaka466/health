from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
TEST_DB_PATH = BACKEND_DIR / "tests" / ".tmp" / "smoke_admin_health_records.sqlite3"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH.as_posix()}")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("RAG_VECTOR_ENABLED", "false")
os.environ.setdefault("HEALTH_DATA_CONTRACT_ADDRESS", "")
os.environ.setdefault("HEALTH_DATA_CONTRACT_ABI_JSON", "")
os.environ.setdefault("OLLAMA_DISABLE_THINKING", "true")

from app.database import Base, SessionLocal, engine
from app.features.auth.service import ensure_admin_user
from app.main import app


class SyncASGIClient:
    def __init__(self, fastapi_app) -> None:
        self.app = fastapi_app
        self.base_url = "http://testserver"

    async def _request_async(self, method: str, url: str, **kwargs):
        transport = httpx.ASGITransport(app=self.app)
        async with httpx.AsyncClient(transport=transport, base_url=self.base_url) as client:
            return await client.request(method, url, **kwargs)

    def request(self, method: str, url: str, **kwargs):
        return asyncio.run(self._request_async(method, url, **kwargs))

    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        ensure_admin_user(db)
    finally:
        db.close()

    client = SyncASGIClient(app)

    register_payload = {
        "username": "smoke_user",
        "email": "smoke_user@example.com",
        "password": "Test123456!",
    }
    register_response = client.post("/api/auth/register", json=register_payload)
    assert_true(register_response.status_code == 200, f"注册失败：{register_response.text}")

    login_response = client.post(
        "/api/auth/login",
        data={"username": register_payload["username"], "password": register_payload["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert_true(login_response.status_code == 200, f"用户登录失败：{login_response.text}")
    user_token = login_response.json()["access_token"]

    create_record_response = client.post(
        "/api/health/records",
        json={
            "data_title": "粗测记录",
            "data_content": json.dumps(
                {"metrics": {"weight": 66, "heart_rate": 72}, "other_text": "仅用于冒烟测试"},
                ensure_ascii=False,
            ),
            "file_type": "text",
            "is_public": False,
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert_true(create_record_response.status_code == 200, f"创建健康记录失败：{create_record_response.text}")

    admin_login_response = client.post(
        "/api/auth/admin/login",
        data={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert_true(admin_login_response.status_code == 200, f"管理员登录失败：{admin_login_response.text}")
    admin_token = admin_login_response.json()["access_token"]

    summary_response = client.get(
        "/api/admin/system/health-records",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert_true(summary_response.status_code == 200, f"管理员健康记录摘要接口失败：{summary_response.text}")

    payload = summary_response.json()
    assert_true(payload["total"] >= 1, "管理员健康记录摘要列表为空")
    assert_true(len(payload["items"]) >= 1, "管理员健康记录摘要项为空")

    first_item = payload["items"][0]
    assert_true(first_item["username"] == "smoke_user", "摘要接口未返回正确用户名")
    assert_true("data_content" not in first_item, "摘要接口泄露了正文 data_content")
    assert_true("pdf_data_base64" not in first_item, "摘要接口泄露了附件内容")
    assert_true("raw_content" not in first_item, "摘要接口泄露了原始内容")

    print("Admin health-record summary smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
