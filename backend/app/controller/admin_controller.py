from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.service.admin_service import AdminSystemService
from app.features.auth.dependencies import get_current_admin
from app.service.auth_service import AuthService
from app.service.blockchain_encryption_service import normalize_private_key, verify_user_private_key
from app.controller.health_data_controller import _serialize_record
from app.schemas import (
    AdminHealthRecordDetailResponse,
    AdminHealthRecordListResponse,
    AdminSystemLogResponse,
    AdminSystemSettings,
    PublicSystemSettings,
)


router = APIRouter()


@router.get("/public-settings", response_model=PublicSystemSettings)
async def get_public_system_settings(db: Session = Depends(get_db)):
    return AdminSystemService(db).get_public_settings()


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


@router.get("/health-records", response_model=AdminHealthRecordListResponse)
async def list_admin_health_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = Query(None),
    file_type: str | None = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    service = AdminSystemService(db)
    service.log(
        level="INFO",
        module="health_records",
        action="view",
        message="管理员查看健康数据上传记录总览",
        operator_id=current_admin.id,
    )
    db.commit()
    return service.list_health_records(
        page=page,
        page_size=page_size,
        keyword=keyword,
        file_type=file_type,
    )


@router.get("/health-records/{record_id}", response_model=AdminHealthRecordDetailResponse)
async def get_admin_health_record_detail(
    record_id: int,
    private_key: str | None = Query(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    record = db.query(models.HealthData).filter(models.HealthData.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="健康数据记录不存在")

    owner = db.query(models.User).filter(models.User.id == record.user_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="记录所属用户不存在")

    normalized_private_key = None
    if private_key:
        wallet_address = AuthService.get_user_wallet_address(owner)
        if not verify_user_private_key(private_key, wallet_address, owner.private_key_hash):
            raise HTTPException(status_code=403, detail="私钥校验失败，无法查看该隐私数据")
        normalized_private_key = normalize_private_key(private_key)

    service = AdminSystemService(db)
    service.log(
        level="INFO",
        module="health_records",
        action="view_detail",
        message=(
            f"管理员查看健康数据详情，记录ID：{record.id}，公开状态："
            f"{'公开' if record.is_public else '私密'}"
        ),
        operator_id=current_admin.id,
    )
    db.commit()

    payload = _serialize_record(record, normalized_private_key, owner)
    payload["username"] = owner.username
    return payload
