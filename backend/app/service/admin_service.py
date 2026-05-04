import json

from sqlalchemy.orm import Session

from app import models
from app.schemas import (
    AdminHealthRecordListResponse,
    AdminHealthRecordSummaryResponse,
    AdminSystemSettings,
    PublicSystemSettings,
)


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

    def get_public_settings(self) -> PublicSystemSettings:
        raw = self.get_settings().model_dump()
        return PublicSystemSettings(**raw)

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

    def list_health_records(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        keyword: str | None = None,
        file_type: str | None = None,
    ) -> AdminHealthRecordListResponse:
        query = self.db.query(models.HealthData, models.User.username).join(
            models.User, models.User.id == models.HealthData.user_id
        )

        trimmed_keyword = (keyword or "").strip()
        if trimmed_keyword:
            like_keyword = f"%{trimmed_keyword}%"
            query = query.filter(models.User.username.ilike(like_keyword))

        normalized_type = (file_type or "").strip().lower()
        if normalized_type in {"text", "pdf", "word"}:
            query = query.filter(models.HealthData.file_type == normalized_type)

        total = query.count()
        rows = (
            query.order_by(models.HealthData.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        items = [
            AdminHealthRecordSummaryResponse(
                id=record.id,
                user_id=record.user_id,
                username=username,
                file_type=record.file_type,
                is_public=bool(record.is_public),
                has_attachment=record.file_type in {"pdf", "word"},
                is_onchain=bool(record.onchain_data_id),
                created_at=record.created_at,
                updated_at=record.updated_at,
            )
            for record, username in rows
        ]

        return AdminHealthRecordListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def log(self, *, level: str, module: str, action: str, message: str, operator_id: int | None = None) -> None:
        if not self._is_operation_log_enabled() and module != "system_settings":
            return

        self.db.add(
            models.SystemLog(
                level=level,
                module=module,
                action=action,
                message=message,
                operator_id=operator_id,
            )
        )

    def _is_operation_log_enabled(self) -> bool:
        row = (
            self.db.query(models.SystemSetting)
            .filter(models.SystemSetting.setting_key == "enable_operation_log")
            .first()
        )
        if not row:
            return True
        return bool(self._parse_value(row.setting_value))

    @staticmethod
    def _parse_value(raw: str):
        try:
            return json.loads(raw)
        except Exception:  # noqa: BLE001
            return raw
