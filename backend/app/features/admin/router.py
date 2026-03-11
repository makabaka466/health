from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.features.admin.service import AdminSystemService
from app.features.auth.dependencies import get_current_admin
from app.schemas import AdminSystemLogResponse, AdminSystemSettings


router = APIRouter()


@router.get("/settings", response_model=AdminSystemSettings)
async def get_admin_system_settings(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    service = AdminSystemService(db)
    service.log(
        level="INFO",
        module="system_settings",
        action="view",
        message="管理员查看系统设置",
        operator_id=current_admin.id,
    )
    db.commit()
    return service.get_settings()


@router.put("/settings", response_model=AdminSystemSettings)
async def update_admin_system_settings(
    payload: AdminSystemSettings,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    service = AdminSystemService(db)
    return service.update_settings(payload, operator_id=current_admin.id)


@router.get("/logs", response_model=list[AdminSystemLogResponse])
async def list_admin_system_logs(
    limit: int = Query(100, ge=1, le=500),
    module: str | None = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    service = AdminSystemService(db)
    service.log(
        level="INFO",
        module="system_logs",
        action="view",
        message="管理员查看系统日志",
        operator_id=current_admin.id,
    )
    db.commit()
    return service.list_logs(limit=limit, module=module)
