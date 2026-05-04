"""
P0 tests: grant/share flow + knowledge/article flow + admin system flow.
"""

from __future__ import annotations

import json

from backend.tests.p0.base import BackendP0TestCase
from app import schemas


class GrantShareP0Tests(BackendP0TestCase):
    def test_private_record_grant_share_and_revoke_flow(self) -> None:
        owner = self.register_user(username="owner_user", email="owner_user@example.com")
        grantee = self.register_user(username="doctor_user", email="doctor_user@example.com")
        owner_login = self.login_user(owner["_raw_username"], owner["_raw_password"])
        grantee_login = self.login_user(grantee["_raw_username"], grantee["_raw_password"])
        owner_headers = self.user_headers(owner_login["access_token"])
        grantee_headers = self.user_headers(grantee_login["access_token"])

        create_record = self.client.post(
            "/api/health/records",
            json={
                "data_title": "private-for-grant",
                "data_content": json.dumps({"metrics": {"weight": 66}, "other_text": "owner private"}, ensure_ascii=False),
                "file_type": "text",
                "is_public": False,
                "private_key": owner["generated_private_key"],
            },
            headers=owner_headers,
        )
        self.assertEqual(create_record.status_code, 200, create_record.text)
        record_id = create_record.json()["id"]

        grantable_users = self.client.get("/api/health/grantable-users", headers=owner_headers)
        self.assertEqual(grantable_users.status_code, 200, grantable_users.text)
        grantable_ids = [item["id"] for item in grantable_users.json()]
        self.assertIn(grantee["id"], grantable_ids)

        create_grant = self.client.post(
            f"/api/health/records/{record_id}/grants",
            params={"private_key": owner["generated_private_key"]},
            json={"grantee_user_id": grantee["id"], "expires_days": 7, "remark": "for consultation"},
            headers=owner_headers,
        )
        self.assertEqual(create_grant.status_code, 200, create_grant.text)
        grant_id = create_grant.json()["id"]

        owner_grants = self.client.get(f"/api/health/records/{record_id}/grants", headers=owner_headers)
        self.assertEqual(owner_grants.status_code, 200, owner_grants.text)
        self.assertEqual(len(owner_grants.json()), 1)

        shared_records = self.client.get("/api/health/shared/records", headers=grantee_headers)
        self.assertEqual(shared_records.status_code, 200, shared_records.text)
        shared_ids = [item["id"] for item in shared_records.json()]
        self.assertIn(record_id, shared_ids)

        shared_detail = self.client.get(f"/api/health/shared/records/{record_id}", headers=grantee_headers)
        self.assertEqual(shared_detail.status_code, 200, shared_detail.text)
        self.assertEqual(shared_detail.json()["id"], record_id)
        self.assertFalse(shared_detail.json()["requires_private_key"])

        revoke = self.client.delete(f"/api/health/grants/{grant_id}", headers=owner_headers)
        self.assertEqual(revoke.status_code, 200, revoke.text)

        shared_after_revoke = self.client.get(f"/api/health/shared/records/{record_id}", headers=grantee_headers)
        self.assertEqual(shared_after_revoke.status_code, 404, shared_after_revoke.text)


class KnowledgeAdminSystemP0Tests(BackendP0TestCase):
    def test_knowledge_article_favorite_and_admin_system_endpoints(self) -> None:
        admin = self.login_admin()
        admin_headers = self.admin_headers(admin["access_token"])
        user = self.register_user(username="reader_user", email="reader_user@example.com")
        user_login = self.login_user(user["_raw_username"], user["_raw_password"])
        user_headers = self.user_headers(user_login["access_token"])

        create_article = self.client.post(
            "/api/knowledge/admin/articles",
            json={
                "title": "P0 Test Article",
                "category": schemas.ARTICLE_CATEGORIES[0],
                "summary": "for test",
                "content": "This is a p0 knowledge article for automated tests.",
                "cover_image": "https://example.com/p0.jpg",
                "tags": ["p0", "test"],
            },
            headers=admin_headers,
        )
        self.assertEqual(create_article.status_code, 200, create_article.text)
        article_id = create_article.json()["id"]

        article_list = self.client.get(
            "/api/knowledge/articles",
            params={"keyword": "P0 Test Article", "page": 1, "page_size": 10},
            headers=user_headers,
        )
        self.assertEqual(article_list.status_code, 200, article_list.text)
        self.assertGreaterEqual(article_list.json()["total"], 1)

        article_detail = self.client.get(f"/api/knowledge/articles/{article_id}", headers=user_headers)
        self.assertEqual(article_detail.status_code, 200, article_detail.text)

        favorite = self.client.post(f"/api/knowledge/articles/{article_id}/favorite", headers=user_headers)
        self.assertEqual(favorite.status_code, 200, favorite.text)
        self.assertTrue(favorite.json()["is_favorited"])

        favorites = self.client.get("/api/knowledge/favorites", headers=user_headers)
        self.assertEqual(favorites.status_code, 200, favorites.text)
        fav_ids = [item["id"] for item in favorites.json()["items"]]
        self.assertIn(article_id, fav_ids)

        history = self.client.get("/api/knowledge/read-history", headers=user_headers)
        self.assertEqual(history.status_code, 200, history.text)
        history_ids = [item["article_id"] for item in history.json()]
        self.assertIn(article_id, history_ids)

        home_reco = self.client.get("/api/knowledge/recommendations/home", headers=user_headers)
        self.assertEqual(home_reco.status_code, 200, home_reco.text)
        self.assertIn("hot_articles", home_reco.json())
        self.assertIn("latest_articles", home_reco.json())

        unfavorite = self.client.delete(f"/api/knowledge/articles/{article_id}/favorite", headers=user_headers)
        self.assertEqual(unfavorite.status_code, 200, unfavorite.text)
        self.assertFalse(unfavorite.json()["is_favorited"])

        # admin system settings / logs / health record overview
        settings_resp = self.client.get("/api/admin/system/settings", headers=admin_headers)
        self.assertEqual(settings_resp.status_code, 200, settings_resp.text)
        settings_payload = settings_resp.json()
        settings_payload["project_name"] = "P0 Test Health System"

        update_settings = self.client.put("/api/admin/system/settings", json=settings_payload, headers=admin_headers)
        self.assertEqual(update_settings.status_code, 200, update_settings.text)
        self.assertEqual(update_settings.json()["project_name"], "P0 Test Health System")

        create_user_record = self.client.post(
            "/api/health/records",
            json={
                "data_title": "admin-view-public-record",
                "data_content": json.dumps({"metrics": {"weight": 61}, "other_text": "public"}, ensure_ascii=False),
                "file_type": "text",
                "is_public": True,
            },
            headers=user_headers,
        )
        self.assertEqual(create_user_record.status_code, 200, create_user_record.text)
        record_id = create_user_record.json()["id"]

        admin_records = self.client.get("/api/admin/system/health-records", headers=admin_headers)
        self.assertEqual(admin_records.status_code, 200, admin_records.text)
        self.assertGreaterEqual(admin_records.json()["total"], 1)

        admin_record_detail = self.client.get(f"/api/admin/system/health-records/{record_id}", headers=admin_headers)
        self.assertEqual(admin_record_detail.status_code, 200, admin_record_detail.text)
        self.assertEqual(admin_record_detail.json()["id"], record_id)

        logs = self.client.get("/api/admin/system/logs", params={"limit": 200}, headers=admin_headers)
        self.assertEqual(logs.status_code, 200, logs.text)
        self.assertGreaterEqual(len(logs.json()), 1)
