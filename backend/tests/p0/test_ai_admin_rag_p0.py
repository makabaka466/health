"""
P0 测试：AI、管理后台与 RAG 核心链路

覆盖内容：
1. 首页 AI 建议生成
2. AI 普通问答 / 流式问答
3. 私密上下文参与问答
4. 管理员新增 RAG 文档
5. chunk / vector 管理接口权限与返回结构
"""

from __future__ import annotations

import json
from unittest.mock import patch

from backend.tests.p0.base import BackendP0TestCase
from app import models
from app.config import settings


class AiAdminRagP0Tests(BackendP0TestCase):
    def test_home_advice_returns_generated_payload_with_updated_at(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        create_record = self.client.post(
            "/api/health/records",
            json={
                "data_title": "首页建议公开记录",
                "data_content": json.dumps(
                    {
                        "metrics": {"weight": 66, "heart_rate": 75},
                        "other_text": "最近状态良好",
                    },
                    ensure_ascii=False,
                ),
                "file_type": "text",
                "is_public": True,
            },
            headers=headers,
        )
        self.assertEqual(create_record.status_code, 200, create_record.text)

        with patch(
            "app.controller.ai_controller._call_ollama",
            return_value=json.dumps(
                {
                    "summary": "这是首页建议摘要",
                    "recommendations": ["每天快走 20 分钟"],
                    "insights": ["结合了近期记录"],
                    "based_on_public_records": 1,
                },
                ensure_ascii=False,
            ),
        ):
            response = self.client.get("/api/ai/home-advice", headers=headers)

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["summary"], "这是首页建议摘要")
        self.assertEqual(payload["based_on_public_records"], 1)
        self.assertTrue(payload["updated_at"])

    def test_ai_chat_returns_references_and_private_context_usage(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        save_profile = self.client.post(
            "/api/auth/me/profile",
            json={
                "profile_data": json.dumps({"medical_history": "asthma"}, ensure_ascii=False),
                "private_key": user["generated_private_key"],
                "is_public": False,
            },
            headers=headers,
        )
        self.assertEqual(save_profile.status_code, 200, save_profile.text)

        private_options = self.client.get("/api/ai/private-context/options", headers=headers)
        self.assertEqual(private_options.status_code, 200, private_options.text)
        option_ids = [item["id"] for item in private_options.json()["items"]]
        self.assertIn("profile:self", option_ids)

        with patch("app.controller.ai_controller._rag_context", return_value=("知识库上下文", ["Knowledge: Demo"])), patch(
            "app.controller.ai_controller._call_ollama",
            return_value="这是 AI 回复",
        ):
            response = self.client.post(
                "/api/ai/chat",
                json={
                    "message": "请结合我的情况给建议",
                    "selected_private_context_ids": ["profile:self"],
                },
                headers=headers,
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["reply"], "这是 AI 回复")
        self.assertEqual(payload["references"], ["Knowledge: Demo"])
        self.assertGreater(payload["private_context_used"], 0)

    def test_ai_chat_stream_emits_sse_events(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        def fake_stream(*args, **kwargs):
            yield "你好"
            yield "，世界"

        with patch("app.controller.ai_controller._rag_context", return_value=("知识库上下文", ["Knowledge: Stream"])), patch(
            "app.controller.ai_controller._stream_ollama",
            side_effect=fake_stream,
        ):
            with self.client.stream(
                "POST",
                "/api/ai/chat/stream",
                json={"message": "请流式回答"},
                headers=headers,
            ) as response:
                self.assertEqual(response.status_code, 200, response.text)
                body = "".join(response.iter_text())

        self.assertIn("event: meta", body)
        self.assertIn("event: status", body)
        self.assertIn("event: delta", body)
        self.assertIn("event: done", body)
        self.assertIn("你好，世界", body)

    def test_admin_can_create_rag_doc_and_inspect_chunk_and_vector_status(self) -> None:
        admin = self.login_admin()
        admin_headers = self.admin_headers(admin["access_token"])

        create_doc = self.client.post(
            "/api/knowledge/admin/rag-docs",
            json={
                "title": "高血压管理说明",
                "category": "慢性病管理",
                "content": "高血压患者应持续监测血压并记录变化。",
                "source": "测试来源",
                "tags": ["高血压", "监测"],
                "is_active": True,
            },
            headers=admin_headers,
        )
        self.assertEqual(create_doc.status_code, 200, create_doc.text)
        doc = create_doc.json()

        db = self.db_session()
        try:
            chunk = models.RagKnowledgeChunk(
                document_id=doc["id"],
                point_id="point-test-1",
                chunk_index=0,
                content="高血压患者应持续监测血压并记录变化。",
                char_count=20,
                is_active=True,
            )
            db.add(chunk)
            db.commit()
            db.refresh(chunk)
            chunk_id = chunk.id
        finally:
            db.close()

        fake_points = [
            {
                "id": "point-test-1",
                "payload": {
                    "document_id": doc["id"],
                    "title": doc["title"],
                    "content": "高血压患者应持续监测血压并记录变化。",
                },
                "vector": [0.11, 0.22, 0.33],
            }
        ]

        with patch.object(settings, "RAG_VECTOR_ENABLED", True), patch(
            "app.controller.knowledge_controller.get_points",
            return_value=fake_points,
        ):
            chunks = self.client.get(
                f"/api/knowledge/admin/rag-docs/{doc['id']}/chunks",
                params={"include_vectors": "true"},
                headers=admin_headers,
            )
            self.assertEqual(chunks.status_code, 200, chunks.text)
            chunks_payload = chunks.json()
            self.assertEqual(chunks_payload["total_chunks"], 1)
            self.assertEqual(chunks_payload["indexed_chunks"], 1)
            self.assertTrue(chunks_payload["items"][0]["vector_exists"])

            vector_detail = self.client.get(
                f"/api/knowledge/admin/rag-chunks/{chunk_id}/vector",
                params={"vector_limit": 2},
                headers=admin_headers,
            )
            self.assertEqual(vector_detail.status_code, 200, vector_detail.text)
            vector_payload = vector_detail.json()
            self.assertEqual(vector_payload["vector_dimension"], 3)
            self.assertEqual(len(vector_payload["vector"]), 2)

    def test_non_admin_cannot_access_rag_chunk_management(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        response = self.client.get(
            "/api/knowledge/admin/rag-docs/1/chunks",
            headers=self.user_headers(login_data["access_token"]),
        )
        self.assertEqual(response.status_code, 403, response.text)
