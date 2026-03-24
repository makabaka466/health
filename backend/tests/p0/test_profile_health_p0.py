"""
P0 测试：用户资料与健康数据模块

覆盖内容：
1. 公开 / 私密资料保存与访问控制
2. 私密资料需要原始私钥解密
3. 公开 / 私密健康记录访问边界
4. 健康数据摘要统计
5. 公开 PDF 记录上传与公共可见性
"""

from __future__ import annotations

import json

from backend.tests.p0.base import BackendP0TestCase


class ProfileAndHealthP0Tests(BackendP0TestCase):
    def test_private_profile_requires_original_private_key_and_public_profile_is_shareable(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        save_private = self.client.post(
            "/api/auth/me/profile",
            json={
                "profile_data": json.dumps({"age": 30, "medical_history": "hypertension"}, ensure_ascii=False),
                "private_key": user["generated_private_key"],
                "is_public": False,
            },
            headers=headers,
        )
        self.assertEqual(save_private.status_code, 200, save_private.text)

        without_private_key = self.client.get("/api/auth/me/profile", headers=headers)
        self.assertEqual(without_private_key.status_code, 400, without_private_key.text)

        with_private_key = self.client.get(
            "/api/auth/me/profile",
            params={"private_key": user["generated_private_key"]},
            headers=headers,
        )
        self.assertEqual(with_private_key.status_code, 200, with_private_key.text)
        self.assertIn("hypertension", with_private_key.json()["profile_data"])

        private_public_access = self.client.get(f"/api/auth/profiles/{user['id']}")
        self.assertEqual(private_public_access.status_code, 403, private_public_access.text)

        save_public = self.client.post(
            "/api/auth/me/profile",
            json={
                "profile_data": json.dumps({"age": 31, "exercise": "walking"}, ensure_ascii=False),
                "private_key": user["generated_private_key"],
                "is_public": True,
            },
            headers=headers,
        )
        self.assertEqual(save_public.status_code, 200, save_public.text)

        public_profile = self.client.get(f"/api/auth/profiles/{user['id']}")
        self.assertEqual(public_profile.status_code, 200, public_profile.text)
        self.assertIn("walking", public_profile.json()["profile_data"])

    def test_public_and_private_health_records_respect_visibility_and_summary(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        public_payload = {
            "data_title": "公开记录",
            "data_content": json.dumps(
                {
                    "metrics": {
                        "weight": 70,
                        "heart_rate": 72,
                        "blood_pressure_systolic": 118,
                        "blood_pressure_diastolic": 78,
                    },
                    "other_text": "状态稳定",
                },
                ensure_ascii=False,
            ),
            "file_type": "text",
            "is_public": True,
        }
        public_record = self.client.post("/api/health/records", json=public_payload, headers=headers)
        self.assertEqual(public_record.status_code, 200, public_record.text)
        public_record_id = public_record.json()["id"]

        private_payload = {
            "data_title": "私密记录",
            "data_content": json.dumps(
                {
                    "metrics": {
                        "weight": 82,
                        "heart_rate": 96,
                    },
                    "other_text": "仅本人可见",
                },
                ensure_ascii=False,
            ),
            "file_type": "text",
            "is_public": False,
            "private_key": user["generated_private_key"],
        }
        private_record = self.client.post("/api/health/records", json=private_payload, headers=headers)
        self.assertEqual(private_record.status_code, 200, private_record.text)
        private_record_id = private_record.json()["id"]

        own_records = self.client.get("/api/health/records", headers=headers)
        self.assertEqual(own_records.status_code, 200, own_records.text)
        self.assertEqual(len(own_records.json()), 2)

        public_records = self.client.get("/api/health/public/records")
        self.assertEqual(public_records.status_code, 200, public_records.text)
        public_ids = [item["id"] for item in public_records.json()]
        self.assertIn(public_record_id, public_ids)
        self.assertNotIn(private_record_id, public_ids)

        private_detail_without_key = self.client.get(f"/api/health/records/{private_record_id}", headers=headers)
        self.assertEqual(private_detail_without_key.status_code, 200, private_detail_without_key.text)
        self.assertTrue(private_detail_without_key.json()["requires_private_key"])

        private_detail_with_key = self.client.get(
            f"/api/health/records/{private_record_id}",
            params={"private_key": user["generated_private_key"]},
            headers=headers,
        )
        self.assertEqual(private_detail_with_key.status_code, 200, private_detail_with_key.text)
        self.assertEqual(private_detail_with_key.json()["data_title"], "私密记录")
        self.assertFalse(private_detail_with_key.json()["requires_private_key"])

        public_private_access = self.client.get(f"/api/health/public/records/{private_record_id}")
        self.assertEqual(public_private_access.status_code, 404, public_private_access.text)

        summary = self.client.get("/api/health/summary", headers=headers)
        self.assertEqual(summary.status_code, 200, summary.text)
        summary_data = summary.json()
        self.assertEqual(summary_data["total_records"], 2)
        self.assertEqual(summary_data["average_weight"], 70)

    def test_pdf_record_can_be_public_and_visible_in_public_feed(self) -> None:
        user = self.register_user()
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        response = self.client.post(
            "/api/health/records",
            json={
                "data_title": "公开 PDF",
                "file_type": "pdf",
                "pdf_data_base64": self.minimal_pdf_base64(),
                "is_public": True,
            },
            headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        record_id = response.json()["id"]

        public_detail = self.client.get(f"/api/health/public/records/{record_id}")
        self.assertEqual(public_detail.status_code, 200, public_detail.text)
        payload = public_detail.json()
        self.assertEqual(payload["file_type"], "pdf")
        self.assertTrue(payload["pdf_data_base64"].startswith("data:application/pdf;base64,"))
