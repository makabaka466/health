#!/usr/bin/env python3
"""
Basic end-to-end API smoke test (requires running backend at 127.0.0.1:8000).
"""

import asyncio
import json
import sys
import uuid

import aiohttp

sys.dont_write_bytecode = True

BASE_URL = "http://127.0.0.1:8000/api"


class HealthSystemTester:
    def __init__(self) -> None:
        self.session: aiohttp.ClientSession | None = None
        self.token: str | None = None
        self.user_data: dict = {}
        self.record_id: int | None = None

    async def setup(self) -> None:
        self.session = aiohttp.ClientSession()
        print("[INFO] setup done")

    async def cleanup(self) -> None:
        if self.session:
            await self.session.close()
        print("[INFO] cleanup done")

    async def test_health_check(self) -> bool:
        assert self.session is not None
        async with self.session.get(f"{BASE_URL}/health") as resp:
            body = await resp.text()
            ok = resp.status == 200
            print(f"[{'PASS' if ok else 'FAIL'}] health_check status={resp.status} body={body[:200]}")
            return ok

    async def test_user_registration(self) -> bool:
        assert self.session is not None
        suffix = uuid.uuid4().hex[:8]
        self.user_data = {
            "username": f"testuser_{suffix}",
            "email": f"test_{suffix}@example.com",
            "password": "Test123456!",
        }
        async with self.session.post(f"{BASE_URL}/auth/register", json=self.user_data) as resp:
            body = await resp.text()
            ok = resp.status == 200
            print(f"[{'PASS' if ok else 'FAIL'}] register status={resp.status} body={body[:220]}")
            return ok

    async def test_user_login(self) -> bool:
        assert self.session is not None
        payload = {"username": self.user_data["username"], "password": self.user_data["password"]}
        for attempt in range(1, 4):
            try:
                async with self.session.post(f"{BASE_URL}/auth/login", data=payload) as resp:
                    body = await resp.text()
                    if resp.status != 200:
                        print(f"[FAIL] login status={resp.status} body={body[:220]}")
                        return False
                    self.token = (await resp.json()).get("access_token")
                    ok = bool(self.token)
                    print(f"[{'PASS' if ok else 'FAIL'}] login status=200 token_received={ok} attempt={attempt}")
                    return ok
            except Exception as exc:  # noqa: BLE001
                print(f"[WARN] login attempt={attempt} exception={exc}")
                await asyncio.sleep(1.2)

        print("[FAIL] login retries exhausted")
        return False

    async def test_get_current_user(self) -> bool:
        assert self.session is not None
        if not self.token:
            print("[FAIL] /auth/me missing token")
            return False
        async with self.session.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {self.token}"},
        ) as resp:
            body = await resp.text()
            ok = resp.status == 200
            print(f"[{'PASS' if ok else 'FAIL'}] auth_me status={resp.status} body={body[:220]}")
            return ok

    async def test_health_data_crud(self) -> bool:
        assert self.session is not None
        if not self.token:
            print("[FAIL] health_crud missing token")
            return False
        headers = {"Authorization": f"Bearer {self.token}"}

        create_payload = {
            "data_title": "脚本测试-公开文本",
            "data_content": json.dumps(
                {
                    "metrics": {
                        "weight": 70.5,
                        "height": 175.0,
                        "blood_pressure_systolic": 120,
                        "blood_pressure_diastolic": 80,
                        "heart_rate": 72,
                        "blood_sugar": 5.2,
                    },
                    "other_text": "basic script create",
                },
                ensure_ascii=False,
            ),
            "file_type": "text",
            "is_public": True,
        }
        async with self.session.post(f"{BASE_URL}/health/records", json=create_payload, headers=headers) as resp:
            body = await resp.text()
            if resp.status != 200:
                print(f"[FAIL] health_create status={resp.status} body={body[:280]}")
                return False
            self.record_id = (await resp.json())["id"]
            print(f"[PASS] health_create id={self.record_id}")

        async with self.session.get(f"{BASE_URL}/health/records", headers=headers) as resp:
            body = await resp.text()
            if resp.status != 200:
                print(f"[FAIL] health_list status={resp.status} body={body[:280]}")
                return False
            print("[PASS] health_list status=200")

        async with self.session.get(f"{BASE_URL}/health/summary", headers=headers) as resp:
            body = await resp.text()
            if resp.status != 200:
                print(f"[FAIL] health_summary status={resp.status} body={body[:280]}")
                return False
            print(f"[PASS] health_summary status=200 body={body[:200]}")

        update_payload = {
            "data_title": "脚本测试-公开文本-更新",
            "data_content": json.dumps(
                {
                    "metrics": {
                        "weight": 71.0,
                        "height": 175.0,
                        "blood_pressure_systolic": 118,
                        "blood_pressure_diastolic": 78,
                        "heart_rate": 70,
                        "blood_sugar": 5.0,
                    },
                    "other_text": "basic script update",
                },
                ensure_ascii=False,
            ),
            "file_type": "text",
            "is_public": True,
        }
        async with self.session.put(
            f"{BASE_URL}/health/records/{self.record_id}",
            json=update_payload,
            headers=headers,
        ) as resp:
            body = await resp.text()
            if resp.status != 200:
                print(f"[FAIL] health_update status={resp.status} body={body[:280]}")
                return False
            print("[PASS] health_update status=200")

        async with self.session.delete(f"{BASE_URL}/health/records/{self.record_id}", headers=headers) as resp:
            body = await resp.text()
            ok = resp.status == 200
            print(f"[{'PASS' if ok else 'FAIL'}] health_delete status={resp.status} body={body[:200]}")
            return ok

    async def test_ai_chat(self) -> bool:
        assert self.session is not None
        if not self.token:
            print("[FAIL] ai_chat missing token")
            return False
        async with self.session.post(
            f"{BASE_URL}/ai/chat",
            json={"message": "什么是正常血压范围？"},
            headers={"Authorization": f"Bearer {self.token}"},
        ) as resp:
            body = await resp.text()
            ok = resp.status == 200
            print(f"[{'PASS' if ok else 'FAIL'}] ai_chat status={resp.status} body={body[:220]}")
            return ok

    async def run_all_tests(self) -> bool:
        tests = [
            ("health_check", self.test_health_check),
            ("register", self.test_user_registration),
            ("login", self.test_user_login),
            ("auth_me", self.test_get_current_user),
            ("health_crud", self.test_health_data_crud),
            ("ai_chat", self.test_ai_chat),
        ]
        passed = 0
        await self.setup()
        for name, fn in tests:
            try:
                ok = await fn()
            except Exception as exc:  # noqa: BLE001
                ok = False
                print(f"[FAIL] {name} exception={exc}")
            if ok:
                passed += 1
        await self.cleanup()
        print(f"[SUMMARY] passed={passed}/{len(tests)}")
        return passed == len(tests)


async def main() -> bool:
    tester = HealthSystemTester()
    return await tester.run_all_tests()


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
