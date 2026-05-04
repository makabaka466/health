#!/usr/bin/env python3
"""
Register/Login smoke test script.
"""

import asyncio
import sys
import uuid

import aiohttp

BASE_URL = "http://127.0.0.1:8000/api"


async def test_register() -> tuple[bool, dict]:
    user_suffix = uuid.uuid4().hex[:8]
    user = {
        "username": f"testuser_{user_suffix}",
        "email": f"testuser_{user_suffix}@example.com",
        "password": "Test123456!",
    }
    print(f"[INFO] register user={user['username']}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{BASE_URL}/auth/register", json=user) as response:
                body = await response.text()
                if response.status == 200:
                    print(f"[PASS] register status=200 body={body[:160]}")
                    return True, user
                print(f"[FAIL] register status={response.status} body={body[:300]}")
                return False, user
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] register exception={exc}")
            return False, user


async def test_login(user: dict) -> bool:
    payload = {"username": user["username"], "password": user["password"]}
    print(f"[INFO] login user={user['username']}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{BASE_URL}/auth/login", data=payload) as response:
                body = await response.text()
                if response.status != 200:
                    print(f"[FAIL] login status={response.status} body={body[:300]}")
                    return False
                token = (await response.json()).get("access_token")
                if not token:
                    print("[FAIL] login missing access_token")
                    return False
                print("[PASS] login status=200 token_received=true")
                async with session.get(
                    f"{BASE_URL}/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                ) as me_resp:
                    me_body = await me_resp.text()
                    if me_resp.status == 200:
                        print(f"[PASS] /auth/me status=200 body={me_body[:160]}")
                        return True
                    print(f"[FAIL] /auth/me status={me_resp.status} body={me_body[:300]}")
                    return False
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] login exception={exc}")
            return False


async def main() -> bool:
    print("== Register/Login Smoke Test ==")
    register_ok, user = await test_register()
    if not register_ok:
        return False
    return await test_login(user)


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)

