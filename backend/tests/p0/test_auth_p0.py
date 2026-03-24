"""
P0 测试：认证与账号模块

覆盖内容：
1. 注册 / 登录主链路
2. 敏感字段脱敏返回
3. 重复用户名 / 邮箱校验
4. 管理员搜索用户、禁用用户、禁止禁用自己
"""

from __future__ import annotations

from backend.tests.p0.base import BackendP0TestCase


class AuthP0Tests(BackendP0TestCase):
    def test_register_and_login_flow_returns_masked_sensitive_fields(self) -> None:
        registered = self.register_user(email="register_flow@example.com")

        self.assertIn("generated_private_key", registered)
        self.assertTrue(registered["generated_private_key"].startswith("0x"))
        self.assertNotEqual(registered["email"], registered["_raw_email"])
        self.assertIn("*", registered["email"])
        self.assertIn("...", registered["wallet_address"])

        login_data = self.login_user(registered["_raw_username"], registered["_raw_password"])
        self.assertIn("access_token", login_data)
        me = self.client.get("/api/auth/me", headers=self.user_headers(login_data["access_token"]))
        self.assertEqual(me.status_code, 200, me.text)
        me_data = me.json()
        self.assertEqual(me_data["username"], registered["_raw_username"])
        self.assertIn("*", me_data["email"])
        self.assertIn("...", me_data["wallet_address"])

    def test_duplicate_username_and_email_are_rejected(self) -> None:
        first = self.register_user(username="dup_user", email="dup_user@example.com")

        duplicate_username = self.client.post(
            "/api/auth/register",
            json={
                "username": first["_raw_username"],
                "email": "another@example.com",
                "password": "Test123456!",
            },
        )
        self.assertEqual(duplicate_username.status_code, 400, duplicate_username.text)

        duplicate_email = self.client.post(
            "/api/auth/register",
            json={
                "username": "another_user",
                "email": first["_raw_email"],
                "password": "Test123456!",
            },
        )
        self.assertEqual(duplicate_email.status_code, 400, duplicate_email.text)

    def test_admin_can_search_by_real_email_disable_user_and_block_login(self) -> None:
        user = self.register_user(email="search_target@example.com")
        admin = self.login_admin()
        admin_headers = self.admin_headers(admin["access_token"])

        search = self.client.get(
            "/api/auth/admin/users",
            params={"keyword": user["_raw_email"]},
            headers=admin_headers,
        )
        self.assertEqual(search.status_code, 200, search.text)
        payload = search.json()
        self.assertGreaterEqual(payload["total"], 1)
        self.assertEqual(payload["items"][0]["username"], user["_raw_username"])
        self.assertIn("*", payload["items"][0]["email"])

        disable = self.client.patch(
            f"/api/auth/admin/users/{user['id']}/status",
            params={"is_active": "false"},
            headers=admin_headers,
        )
        self.assertEqual(disable.status_code, 200, disable.text)
        self.assertFalse(disable.json()["is_active"])

        blocked_login = self.client.post(
            "/api/auth/login",
            data={"username": user["_raw_username"], "password": user["_raw_password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(blocked_login.status_code, 403, blocked_login.text)

    def test_admin_cannot_disable_self(self) -> None:
        admin = self.login_admin()
        response = self.client.patch(
            "/api/auth/admin/users/1/status",
            params={"is_active": "false"},
            headers=self.admin_headers(admin["access_token"]),
        )
        self.assertEqual(response.status_code, 400, response.text)
