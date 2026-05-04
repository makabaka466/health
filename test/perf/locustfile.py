import json
import os
import random
import time
import uuid

from locust import HttpUser, between, tag, task


BASE_PATH = os.getenv("BASE_PATH", "/api")
LOGIN_USERNAME = os.getenv("LOGIN_USERNAME", "xiaoming")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "123456")


def _now_ms() -> int:
    return int(time.time() * 1000)


class AuthenticatedUser(HttpUser):
    wait_time = between(0.5, 2.0)
    token = None

    def on_start(self):
        # 1) try admin/user login endpoint (form encoded)
        # 2) store bearer token for subsequent requests
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
            try:
                payload = resp.json()
            except Exception as exc:  # noqa: BLE001
                resp.failure(f"login parse failed: {exc}")
                return

            token = payload.get("access_token")
            if not token:
                resp.failure("login missing access_token")
                return

            self.token = token
            resp.success()

    @property
    def auth_headers(self):
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}


class NormalApiUser(AuthenticatedUser):
    """
    普通业务接口并发（读多+少量写）
    建议用于 5.5 表5-7。
    """

    @tag("normal", "read")
    @task(4)
    def health_records_list(self):
        self.client.get(
            f"{BASE_PATH}/health/records",
            headers=self.auth_headers,
            name="health:list",
        )

    @tag("normal", "read")
    @task(4)
    def knowledge_articles_list(self):
        self.client.get(
            f"{BASE_PATH}/knowledge/articles?page=1&page_size=10",
            headers=self.auth_headers,
            name="knowledge:list",
        )

    @tag("normal", "read")
    @task(2)
    def health_summary(self):
        self.client.get(
            f"{BASE_PATH}/health/summary",
            headers=self.auth_headers,
            name="health:summary",
        )

    @tag("normal", "write")
    @task(1)
    def create_health_record(self):
        payload = {
            "data_title": f"locust-{uuid.uuid4().hex[:8]}",
            "data_content": json.dumps(
                {
                    "metrics": {
                        "weight": round(random.uniform(55, 85), 1),
                        "heart_rate": random.randint(60, 95),
                        "blood_pressure_systolic": random.randint(105, 140),
                        "blood_pressure_diastolic": random.randint(65, 90),
                    },
                    "other_text": f"locust-generated-{_now_ms()}",
                },
                ensure_ascii=False,
            ),
            "file_type": "text",
            "is_public": True,
        }
        self.client.post(
            f"{BASE_PATH}/health/records",
            json=payload,
            headers=self.auth_headers,
            name="health:create_text",
        )


class AiApiUser(AuthenticatedUser):
    """
    AI 问答接口并发（单独压测）
    建议用于 5.5 表5-8。
    """

    wait_time = between(1.0, 3.0)

    @tag("ai")
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
        self.client.post(
            f"{BASE_PATH}/ai/chat",
            json=payload,
            headers=self.auth_headers,
            name="ai:chat",
        )
