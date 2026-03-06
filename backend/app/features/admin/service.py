import json

from sqlalchemy.orm import Session

from app import models
from app.schemas import AdminSystemSettings


DEFAULT_SETTINGS = AdminSystemSettings().model_dump()


class AdminSystemService:
    def __init__(self, db: Session):
        self.db = db

    def get_settings(self) -> AdminSystemSettings:
        rows = self.db.query(models.SystemSetting).all()
        if not rows:
            return AdminSystemSettings()

        payload = {item.setting_key: self._parse_value(item.setting_value) for item in rows}
        return AdminSystemSettings(**{**DEFAULT_SETTINGS, **payload})

    def update_settings(self, settings: AdminSystemSettings, operator_id: int | None = None) -> AdminSystemSettings:
        data = settings.model_dump()
        for key, value in data.items():
            row = self.db.query(models.SystemSetting).filter(models.SystemSetting.setting_key == key).first()
            serialized = json.dumps(value, ensure_ascii=False)
            if row:
                row.setting_value = serialized
                row.updated_by = operator_id
            else:
                self.db.add(
                    models.SystemSetting(
                        setting_key=key,
                        setting_value=serialized,
                        updated_by=operator_id,
                    )
                )

        self.log(
            level="INFO",
            module="system_settings",
            action="update",
            message="管理员更新系统设置",
            operator_id=operator_id,
        )

        self.db.commit()
        return self.get_settings()

    def list_logs(self, limit: int = 100, module: str | None = None):
        query = self.db.query(models.SystemLog)
        if module:
            query = query.filter(models.SystemLog.module == module)
        return query.order_by(models.SystemLog.created_at.desc()).limit(limit).all()

    def log(self, *, level: str, module: str, action: str, message: str, operator_id: int | None = None) -> None:
        self.db.add(
            models.SystemLog(
                level=level,
                module=module,
                action=action,
                message=message,
                operator_id=operator_id,
            )
        )

    @staticmethod
    def _parse_value(raw: str):
        try:
            return json.loads(raw)
        except Exception:  # noqa: BLE001
            return raw
