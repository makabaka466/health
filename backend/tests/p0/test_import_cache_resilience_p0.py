"""
P0/P1 测试：导入、缓存失效与异常韧性

覆盖内容：
1. 管理员导入 DOCX 文章
2. 管理员导入 DOCX RAG 文档
3. 首页 AI 建议缓存生成后，公开健康记录更新会使缓存失效
4. Ollama 不可用时普通问答返回 503
5. Ollama 不可用时流式问答返回 error 事件
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from backend.tests.p0.base import BackendP0TestCase
from app import models


class ImportCacheResilienceTests(BackendP0TestCase):
    def test_admin_can_import_articles_from_docx(self) -> None:
        admin = self.login_admin()
        sample_docx = Path(__file__).resolve().parents[3] / "test" / "article-import-demo.docx"
        self.assertTrue(sample_docx.exists(), "缺少测试导入文件 article-import-demo.docx")

        with sample_docx.open("rb") as fh:
            response = self.client.post(
                "/api/knowledge/admin/articles/import",
                data={
                    "category": "饮食营养",
                    "tags": "测试导入,文章",
                    "cover_image": "https://example.com/demo.jpg",
                },
                files={"files": (sample_docx.name, fh.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                headers=self.admin_headers(admin["access_token"]),
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["imported_count"], 1)
        self.assertEqual(payload["items"][0]["title"], "article-import-demo")
        self.assertEqual(payload["items"][0]["category"], "饮食营养")

    def test_admin_can_import_rag_docs_from_docx(self) -> None:
        admin = self.login_admin()
        sample_docx = Path(__file__).resolve().parents[3] / "test" / "article-import-demo.docx"

        with sample_docx.open("rb") as fh:
            response = self.client.post(
                "/api/knowledge/admin/rag-docs/import",
                data={
                    "category": "慢性病管理",
                    "tags": "测试导入,知识库",
                    "source": "本地测试文件",
                    "is_active": "true",
                },
                files={"files": (sample_docx.name, fh.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                headers=self.admin_headers(admin["access_token"]),
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["imported_count"], 1)
        self.assertEqual(payload["items"][0]["title"], "article-import-demo")
        self.assertEqual(payload["items"][0]["source"], "本地测试文件")

    def test_home_advice_cache_is_invalidated_after_public_record_update(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        create_record = self.client.post(
            "/api/health/records",
            json={
                "data_title": "公开记录",
                "data_content": json.dumps(
                    {"metrics": {"weight": 60, "heart_rate": 70}, "other_text": "首次记录"},
                    ensure_ascii=False,
                ),
                "file_type": "text",
                "is_public": True,
            },
            headers=headers,
        )
        self.assertEqual(create_record.status_code, 200, create_record.text)
        record_id = create_record.json()["id"]

        with patch(
            "app.controller.ai_controller._call_ollama",
            return_value=json.dumps(
                {
                    "summary": "缓存已生成",
                    "recommendations": ["保持规律作息"],
                    "insights": ["基于公开记录"],
                    "based_on_public_records": 1,
                },
                ensure_ascii=False,
            ),
        ):
            advice = self.client.get("/api/ai/home-advice", headers=headers)
        self.assertEqual(advice.status_code, 200, advice.text)

        db = self.db_session()
        try:
            db_user = db.query(models.User).filter(models.User.id == user["id"]).first()
            self.assertIsNotNone(db_user.home_ai_advice_cache)
        finally:
            db.close()

        update_record = self.client.put(
            f"/api/health/records/{record_id}",
            json={
                "data_title": "公开记录更新后",
                "data_content": json.dumps(
                    {"metrics": {"weight": 61, "heart_rate": 72}, "other_text": "更新后记录"},
                    ensure_ascii=False,
                ),
                "file_type": "text",
                "is_public": True,
            },
            headers=headers,
        )
        self.assertEqual(update_record.status_code, 200, update_record.text)

        db = self.db_session()
        try:
            db_user = db.query(models.User).filter(models.User.id == user["id"]).first()
            self.assertIsNone(db_user.home_ai_advice_cache)
        finally:
            db.close()

    def test_ai_chat_returns_503_when_ollama_unavailable(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])

        with patch("app.controller.ai_controller._call_ollama", side_effect=RuntimeError("Ollama 连接失败")):
            response = self.client.post(
                "/api/ai/chat",
                json={"message": "你好"},
                headers=self.user_headers(login_data["access_token"]),
            )

        self.assertEqual(response.status_code, 503, response.text)

    def test_ai_stream_returns_error_event_when_ollama_unavailable(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])

        def broken_stream(*args, **kwargs):
            raise RuntimeError("Ollama 连接失败")
            yield  # pragma: no cover

        with patch("app.controller.ai_controller._stream_ollama", side_effect=broken_stream):
            with self.client.stream(
                "POST",
                "/api/ai/chat/stream",
                json={"message": "请流式回答"},
                headers=self.user_headers(login_data["access_token"]),
            ) as response:
                self.assertEqual(response.status_code, 200, response.text)
                body = "".join(response.iter_text())

        self.assertIn("event: error", body)
        self.assertIn("Ollama", body)
