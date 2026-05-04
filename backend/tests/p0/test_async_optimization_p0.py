"""
P0 异步优化回归测试

覆盖内容：
1. 健康记录上链写入通过 asyncio.to_thread 调用
2. 文章导入解析通过 asyncio.to_thread 调用
3. RAG 文档导入解析通过 asyncio.to_thread 调用
4. 新建 RAG 文档会触发后台索引任务入队
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from backend.tests.p0.base import BackendP0TestCase


class AsyncOptimizationP0Tests(BackendP0TestCase):
    def test_create_private_health_record_uses_to_thread_for_chain_write(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        fake_to_thread = AsyncMock(return_value={"tx_hash": "0xabc", "data_id": "0x" + ("1" * 64)})
        with patch("app.controller.health_data_controller.asyncio.to_thread", fake_to_thread):
            response = self.client.post(
                "/api/health/records",
                json={
                    "data_title": "异步上链测试",
                    "data_content": '{"metrics":{"weight":66}}',
                    "file_type": "text",
                    "is_public": False,
                    "private_key": user["generated_private_key"],
                },
                headers=headers,
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertGreaterEqual(fake_to_thread.await_count, 1)

    def test_import_articles_uses_to_thread_for_document_parse(self) -> None:
        admin = self.login_admin()
        admin_headers = self.admin_headers(admin["access_token"])

        fake_to_thread = AsyncMock(return_value="这是一段导入文章内容")
        with patch("app.controller.knowledge_controller.asyncio.to_thread", fake_to_thread):
            response = self.client.post(
                "/api/knowledge/admin/articles/import",
                data={"category": "饮食营养", "tags": "异步,测试"},
                files={
                    "files": (
                        "async-import.docx",
                        b"fake-docx-binary",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
                headers=admin_headers,
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json().get("imported_count"), 1)
        self.assertGreaterEqual(fake_to_thread.await_count, 1)

    def test_import_rag_docs_uses_to_thread_for_document_parse(self) -> None:
        admin = self.login_admin()
        admin_headers = self.admin_headers(admin["access_token"])

        fake_to_thread = AsyncMock(return_value="这是一段导入知识库文档内容")
        with patch("app.controller.knowledge_controller.asyncio.to_thread", fake_to_thread):
            response = self.client.post(
                "/api/knowledge/admin/rag-docs/import",
                data={"category": "慢性病管理", "source": "异步测试", "tags": "异步,测试", "is_active": "true"},
                files={
                    "files": (
                        "async-rag.docx",
                        b"fake-docx-binary",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
                headers=admin_headers,
            )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json().get("imported_count"), 1)
        self.assertGreaterEqual(fake_to_thread.await_count, 1)

    def test_create_rag_doc_enqueues_background_sync_task(self) -> None:
        admin = self.login_admin()
        admin_headers = self.admin_headers(admin["access_token"])

        with patch("app.controller.knowledge_controller._enqueue_rag_sync") as enqueue_mock:
            response = self.client.post(
                "/api/knowledge/admin/rag-docs",
                json={
                    "title": "异步入队测试文档",
                    "category": "慢性病管理",
                    "content": "用于验证后台索引任务入队。",
                    "source": "test",
                    "tags": ["异步", "入队"],
                    "is_active": True,
                },
                headers=admin_headers,
            )

        self.assertEqual(response.status_code, 200, response.text)
        enqueue_mock.assert_called_once()

