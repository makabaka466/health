from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
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
    visibility: str | None = Query(None),
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
        visibility=visibility,
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

    now = datetime.utcnow()
    active_grant = (
        db.query(models.HealthDataGrant)
        .filter(
            models.HealthDataGrant.record_id == record.id,
            models.HealthDataGrant.grantee_user_id == current_admin.id,
            models.HealthDataGrant.can_read.is_(True),
            models.HealthDataGrant.revoked_at.is_(None),
            or_(models.HealthDataGrant.expires_at.is_(None), models.HealthDataGrant.expires_at > now),
        )
        .order_by(models.HealthDataGrant.created_at.desc())
        .first()
    )

    payload = None
    authorized_via_grant = False
    # 优先使用管理员授权记录中的 wrapped_dek 解密私密数据。
    if active_grant and not record.is_public:
        admin_private_key = None
        if private_key:
            admin_wallet = AuthService.get_user_wallet_address(current_admin)
            if verify_user_private_key(private_key, admin_wallet, current_admin.private_key_hash):
                admin_private_key = normalize_private_key(private_key)

        if not admin_private_key and current_admin.encrypted_private_key:
            try:
                admin_private_key = normalize_private_key(
                    AuthService.decrypt_private_key_from_storage(current_admin.encrypted_private_key)
                )
            except ValueError:
                admin_private_key = None

        if admin_private_key:
            payload = _serialize_record(
                record,
                admin_private_key,
                current_user=current_admin,
                wrapped_dek=active_grant.wrapped_dek,
            )
            authorized_via_grant = True

    # 未通过授权解密时，回退到所有者私钥序列化记录。
    if payload is None:
        normalized_owner_private_key = None
        if private_key:
            owner_wallet_address = AuthService.get_user_wallet_address(owner)
            if verify_user_private_key(private_key, owner_wallet_address, owner.private_key_hash):
                normalized_owner_private_key = normalize_private_key(private_key)
        payload = _serialize_record(record, normalized_owner_private_key, owner)

    service = AdminSystemService(db)
    service.log(
        level="INFO",
        module="health_records",
        action="view_detail",
        message=(
            f"管理员查看健康数据记录详情，ID：{record.id}，可见性："
            f"{'公开' if record.is_public else '私密'}"
        ),
        operator_id=current_admin.id,
        force=True,
    )
    db.commit()

    payload["username"] = owner.username
    payload["authorized_via_grant"] = authorized_via_grant
    return payload
