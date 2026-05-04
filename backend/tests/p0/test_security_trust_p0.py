"""
Security & trust tests for chapter 5.4 (S-01 ~ S-10).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from unittest.mock import patch

from jose import jwt

from backend.tests.p0.base import BackendP0TestCase
from app import models
from app.config import settings
from app.controller.health_data_controller import _build_source_payload, _hash_payload, _public_storage_key
from app.service.blockchain_encryption_service import encrypt_text


class SecurityTrustP0Tests(BackendP0TestCase):
    def _create_private_record(self, owner_headers: dict[str, str], private_key: str) -> int:
        response = self.client.post(
            "/api/health/records",
            json={
                "data_title": "security-private-record",
                "data_content": json.dumps({"metrics": {"weight": 65}, "other_text": "private"}, ensure_ascii=False),
                "file_type": "text",
                "is_public": False,
                "private_key": private_key,
            },
            headers=owner_headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["id"]

    def test_s01_private_data_not_visible_in_public_endpoint(self) -> None:
        owner = self.register_user(username="s01_owner", email="s01_owner@example.com")
        owner_login = self.login_user(owner["_raw_username"], owner["_raw_password"])
        owner_headers = self.user_headers(owner_login["access_token"])
        record_id = self._create_private_record(owner_headers, owner["generated_private_key"])

        public_detail = self.client.get(f"/api/health/public/records/{record_id}")
        self.assertEqual(public_detail.status_code, 404, public_detail.text)

    def test_s02_owner_can_decrypt_private_record(self) -> None:
        owner = self.register_user(username="s02_owner", email="s02_owner@example.com")
        owner_login = self.login_user(owner["_raw_username"], owner["_raw_password"])
        owner_headers = self.user_headers(owner_login["access_token"])
        record_id = self._create_private_record(owner_headers, owner["generated_private_key"])

        detail = self.client.get(f"/api/health/records/{record_id}", headers=owner_headers)
        self.assertEqual(detail.status_code, 200, detail.text)
        payload = detail.json()
        self.assertFalse(payload["requires_private_key"])
        self.assertIn("weight", payload["data_content"])

    def test_s03_authorized_user_can_read_shared_private_record(self) -> None:
        owner = self.register_user(username="s03_owner", email="s03_owner@example.com")
        grantee = self.register_user(username="s03_doctor", email="s03_doctor@example.com")
        owner_login = self.login_user(owner["_raw_username"], owner["_raw_password"])
        grantee_login = self.login_user(grantee["_raw_username"], grantee["_raw_password"])
        owner_headers = self.user_headers(owner_login["access_token"])
        grantee_headers = self.user_headers(grantee_login["access_token"])
        record_id = self._create_private_record(owner_headers, owner["generated_private_key"])

        grant_resp = self.client.post(
            f"/api/health/records/{record_id}/grants",
            params={"private_key": owner["generated_private_key"]},
            json={"grantee_user_id": grantee["id"], "expires_days": 7, "remark": "s03"},
            headers=owner_headers,
        )
        self.assertEqual(grant_resp.status_code, 200, grant_resp.text)

        shared_detail = self.client.get(f"/api/health/shared/records/{record_id}", headers=grantee_headers)
        self.assertEqual(shared_detail.status_code, 200, shared_detail.text)
        self.assertFalse(shared_detail.json()["requires_private_key"])

    def test_s04_revoked_grant_cannot_be_used(self) -> None:
        owner = self.register_user(username="s04_owner", email="s04_owner@example.com")
        grantee = self.register_user(username="s04_doctor", email="s04_doctor@example.com")
        owner_login = self.login_user(owner["_raw_username"], owner["_raw_password"])
        grantee_login = self.login_user(grantee["_raw_username"], grantee["_raw_password"])
        owner_headers = self.user_headers(owner_login["access_token"])
        grantee_headers = self.user_headers(grantee_login["access_token"])
        record_id = self._create_private_record(owner_headers, owner["generated_private_key"])

        grant_resp = self.client.post(
            f"/api/health/records/{record_id}/grants",
            params={"private_key": owner["generated_private_key"]},
            json={"grantee_user_id": grantee["id"], "expires_days": 7, "remark": "s04"},
            headers=owner_headers,
        )
        self.assertEqual(grant_resp.status_code, 200, grant_resp.text)
        grant_id = grant_resp.json()["id"]

        revoke = self.client.delete(f"/api/health/grants/{grant_id}", headers=owner_headers)
        self.assertEqual(revoke.status_code, 200, revoke.text)

        shared_detail = self.client.get(f"/api/health/shared/records/{record_id}", headers=grantee_headers)
        self.assertEqual(shared_detail.status_code, 404, shared_detail.text)

    def test_s05_expired_grant_cannot_be_used(self) -> None:
        owner = self.register_user(username="s05_owner", email="s05_owner@example.com")
        grantee = self.register_user(username="s05_doctor", email="s05_doctor@example.com")
        owner_login = self.login_user(owner["_raw_username"], owner["_raw_password"])
        grantee_login = self.login_user(grantee["_raw_username"], grantee["_raw_password"])
        owner_headers = self.user_headers(owner_login["access_token"])
        grantee_headers = self.user_headers(grantee_login["access_token"])
        record_id = self._create_private_record(owner_headers, owner["generated_private_key"])

        grant_resp = self.client.post(
            f"/api/health/records/{record_id}/grants",
            params={"private_key": owner["generated_private_key"]},
            json={"grantee_user_id": grantee["id"], "expires_days": 1, "remark": "s05"},
            headers=owner_headers,
        )
        self.assertEqual(grant_resp.status_code, 200, grant_resp.text)
        grant_id = grant_resp.json()["id"]

        db = self.db_session()
        try:
            grant = db.query(models.HealthDataGrant).filter(models.HealthDataGrant.id == grant_id).first()
            grant.expires_at = datetime.utcnow() - timedelta(minutes=1)
            db.commit()
        finally:
            db.close()

        shared_detail = self.client.get(f"/api/health/shared/records/{record_id}", headers=grantee_headers)
        self.assertEqual(shared_detail.status_code, 404, shared_detail.text)

    def test_s06_logs_do_not_leak_private_key_plaintext(self) -> None:
        owner = self.register_user(username="s06_owner", email="s06_owner@example.com")
        owner_login = self.login_user(owner["_raw_username"], owner["_raw_password"])
        owner_headers = self.user_headers(owner_login["access_token"])
        _ = self._create_private_record(owner_headers, owner["generated_private_key"])

        admin = self.login_admin()
        admin_headers = self.admin_headers(admin["access_token"])
        logs = self.client.get("/api/admin/system/logs", params={"limit": 200}, headers=admin_headers)
        self.assertEqual(logs.status_code, 200, logs.text)
        all_messages = " ".join(item.get("message", "") for item in logs.json())

        self.assertNotIn(owner["generated_private_key"], all_messages)
        self.assertNotIn("private_key", all_messages.lower())

    def test_s07_onchain_verification_passes_when_hash_matches(self) -> None:
        user = self.register_user(username="s07_user", email="s07_user@example.com")
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        source_content = json.dumps({"metrics": {"weight": 61}, "other_text": "onchain-pass"}, ensure_ascii=False)
        create_record = self.client.post(
            "/api/health/records",
            json={
                "data_title": "s07-public",
                "data_content": source_content,
                "file_type": "text",
                "is_public": True,
            },
            headers=headers,
        )
        self.assertEqual(create_record.status_code, 200, create_record.text)
        record_id = create_record.json()["id"]

        payload = _build_source_payload("text", data_content=source_content)
        expected_hash = _hash_payload(payload)

        db = self.db_session()
        try:
            record = db.query(models.HealthData).filter(models.HealthData.id == record_id).first()
            record.onchain_data_id = "0x" + ("1" * 64)
            db.commit()
        finally:
            db.close()

        with patch("app.controller.health_data_controller.chain_service") as mock_chain:
            mock_chain.enabled = True
            mock_chain.get_health_record.return_value = {"data_hash": expected_hash}
            detail = self.client.get(f"/api/health/records/{record_id}", headers=headers)
            self.assertEqual(detail.status_code, 200, detail.text)
            self.assertTrue(detail.json()["onchain_verified"])
            self.assertEqual(detail.json()["onchain_verification_status"], "verified")

    def test_s08_onchain_verification_fails_after_tamper(self) -> None:
        user = self.register_user(username="s08_user", email="s08_user@example.com")
        login_data = self.login_user(user["_raw_username"], user["_raw_password"])
        headers = self.user_headers(login_data["access_token"])

        original_content = json.dumps({"metrics": {"weight": 62}, "other_text": "onchain-original"}, ensure_ascii=False)
        create_record = self.client.post(
            "/api/health/records",
            json={
                "data_title": "s08-public",
                "data_content": original_content,
                "file_type": "text",
                "is_public": True,
            },
            headers=headers,
        )
        self.assertEqual(create_record.status_code, 200, create_record.text)
        record_id = create_record.json()["id"]

        payload = _build_source_payload("text", data_content=original_content)
        expected_hash = _hash_payload(payload)

        db = self.db_session()
        try:
            record = db.query(models.HealthData).filter(models.HealthData.id == record_id).first()
            record.onchain_data_id = "0x" + ("2" * 64)
            tampered_content = json.dumps({"metrics": {"weight": 200}, "other_text": "tampered"}, ensure_ascii=False)
            record.encrypted_data_content = encrypt_text(tampered_content, _public_storage_key())
            db.commit()
        finally:
            db.close()

        with patch("app.controller.health_data_controller.chain_service") as mock_chain:
            mock_chain.enabled = True
            mock_chain.get_health_record.return_value = {"data_hash": expected_hash}
            detail = self.client.get(f"/api/health/records/{record_id}", headers=headers)
            self.assertEqual(detail.status_code, 200, detail.text)
            self.assertFalse(detail.json()["onchain_verified"])
            self.assertEqual(detail.json()["onchain_verification_status"], "mismatch")

    def test_s09_cross_user_access_is_forbidden(self) -> None:
        owner = self.register_user(username="s09_owner", email="s09_owner@example.com")
        attacker = self.register_user(username="s09_attacker", email="s09_attacker@example.com")
        owner_login = self.login_user(owner["_raw_username"], owner["_raw_password"])
        attacker_login = self.login_user(attacker["_raw_username"], attacker["_raw_password"])
        owner_headers = self.user_headers(owner_login["access_token"])
        attacker_headers = self.user_headers(attacker_login["access_token"])

        record_id = self._create_private_record(owner_headers, owner["generated_private_key"])
        attacker_read = self.client.get(f"/api/health/records/{record_id}", headers=attacker_headers)
        self.assertEqual(attacker_read.status_code, 404, attacker_read.text)

    def test_s10_token_validation_for_missing_invalid_and_expired(self) -> None:
        # missing token
        no_token = self.client.get("/api/health/records")
        self.assertEqual(no_token.status_code, 401, no_token.text)

        # invalid token
        bad_token = self.client.get("/api/health/records", headers={"Authorization": "Bearer invalid.token.value"})
        self.assertEqual(bad_token.status_code, 401, bad_token.text)

        # expired token
        expired = jwt.encode(
            {"sub": "admin", "exp": datetime.utcnow() - timedelta(minutes=5)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        expired_resp = self.client.get("/api/health/records", headers={"Authorization": f"Bearer {expired}"})
        self.assertEqual(expired_resp.status_code, 401, expired_resp.text)
