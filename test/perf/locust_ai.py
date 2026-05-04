import os
import random

from locust import HttpUser, between, task


BASE_PATH = os.getenv("BASE_PATH", "/api")
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME", "xiaoming")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "123456")


class AiApiUser(HttpUser):
    wait_time = between(1.0, 3.0)
    token = None

    def on_start(self):
        with self.client.post(
            f"{BASE_PATH}/auth/login",
            data={"username": LOGIN_USERNAME, "password": LOGIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            name="auth:login",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"login failed: {resp.status_code} {resp.text[:120]}")
                return
            payload = resp.json()
            token = payload.get("access_token")
            if not token:
                resp.failure("login missing access_token")
                return
            self.token = token
            resp.success()

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task
    def ai_chat(self):
        payload = {
            "message": random.choice(
                [
                    "什么是正常血压范围？",
                    "如何控制体重更科学？",
                    "心率偏快应该注意什么？",
                    "我最近睡眠差，有什么建议？",
                ]
            )
        }
        self.client.post(f"{BASE_PATH}/ai/chat", json=payload, headers=self.auth_headers, name="ai:chat")

