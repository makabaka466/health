import asyncio
import base64
import hashlib
import json
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app import models, schemas
from app.service.admin_service import AdminSystemService
from app.service.ai_service import invalidate_user_home_advice
from app.features.auth.dependencies import get_current_user
from app.service.auth_service import AuthService
from app.service.blockchain_service import chain_service
from app.service.blockchain_encryption_service import (
    decrypt_binary,
    decrypt_binary_with_dek,
    decrypt_text,
    decrypt_text_with_dek,
    encrypt_binary,
    encrypt_binary_with_dek,
    encrypt_text,
    encrypt_text_with_dek,
    generate_data_encryption_key,
    normalize_private_key,
    private_key_to_public_key,
    rewrap_dek_for_recipient,
    unwrap_dek_with_private_key,
    verify_user_private_key,
    wrap_dek_for_public_key,
)


router = APIRouter()

PDF_MIME_TYPES = {"application/pdf", "application/octet-stream"}
WORD_MIME_TYPES = {
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",
}
UPLOAD_SIZE_LIMITS = {
    "pdf": 6 * 1024 * 1024,
    "word": 10 * 1024 * 1024,
}


def _invalidate_home_advice_if_needed(db: Session, user: models.User, should_refresh: bool) -> None:
    if should_refresh:
        invalidate_user_home_advice(db, user)


def _get_bool_system_setting(db: Session, key: str, default_value: bool) -> bool:
    row = db.query(models.SystemSetting).filter(models.SystemSetting.setting_key == key).first()
    if not row:
        return default_value
    try:
        value = json.loads(row.setting_value)
    except Exception:  # noqa: BLE001
        return default_value
    return bool(value)


def _normalized_file_type(file_type: Optional[str]) -> str:
    normalized = (file_type or "text").strip().lower()
    return normalized if normalized in {"text", "pdf", "word"} else "text"


def _default_mime_type(file_type: str) -> Optional[str]:
    if file_type == "pdf":
        return "application/pdf"
    if file_type == "word":
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return None


# 功能说明：解析上传文件并校验类型和大小。
def _decode_upload_data(file_type: str, file_data_base64: Optional[str]) -> tuple[Optional[bytes], Optional[int], Optional[str]]:
    if file_type == "text":
        return None, None, None

    if not file_data_base64:
        return None, None, None

    raw_value = file_data_base64.strip()
    if not raw_value:
        return None, None, None

    detected_mime_type = _default_mime_type(file_type)
    if "," in raw_value:
        prefix, encoded_value = raw_value.split(",", 1)
        mime_type = prefix.split(":", 1)[-1].split(";", 1)[0].strip().lower() if ":" in prefix else ""
        allowed_mime_types = PDF_MIME_TYPES if file_type == "pdf" else WORD_MIME_TYPES
        if mime_type and mime_type not in allowed_mime_types:
            if file_type == "pdf":
                raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")
            raise HTTPException(status_code=400, detail="仅支持 Word 格式文件（.doc/.docx）")
        detected_mime_type = _default_mime_type(file_type) if mime_type == "application/octet-stream" else (mime_type or detected_mime_type)
    else:
        encoded_value = raw_value

    try:
        decoded = base64.b64decode(encoded_value, validate=True)
    except Exception as exc:  # noqa: BLE001
        if file_type == "pdf":
            raise HTTPException(status_code=400, detail="PDF 文件内容非法") from exc
        raise HTTPException(status_code=400, detail="Word 文件内容非法") from exc

    if file_type == "pdf" and not decoded.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")
    if file_type == "word":
        is_doc = decoded.startswith(bytes.fromhex("D0CF11E0A1B11AE1"))
        is_docx = decoded.startswith(b"PK")
        if not (is_doc or is_docx):
            raise HTTPException(status_code=400, detail="仅支持 Word 格式文件（.doc/.docx）")

    size_limit = UPLOAD_SIZE_LIMITS.get(file_type, 6 * 1024 * 1024)
    if len(decoded) > size_limit:
        if file_type == "pdf":
            raise HTTPException(status_code=400, detail="PDF 文件过大，请压缩后再上传")
        raise HTTPException(status_code=400, detail="Word 文件过大，请压缩后再上传")

    return decoded, len(decoded), detected_mime_type or _default_mime_type(file_type)


def _extract_metrics(content: Optional[str]) -> dict:
    if not content:
        return {}
    try:
        payload = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return {}
    return payload.get("metrics", {}) if isinstance(payload, dict) else {}


def _resolve_effective_private_key(user: models.User, private_key: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    explicit_private_key = _validate_explicit_private_key(user, private_key)
    if explicit_private_key:
        return explicit_private_key, explicit_private_key

    if user.encrypted_private_key:
        try:
            resolved_private_key = normalize_private_key(
                AuthService.decrypt_private_key_from_storage(user.encrypted_private_key)
            )
            return resolved_private_key, resolved_private_key
        except ValueError:
            pass

    legacy_private_key = _legacy_private_storage_key(user)
    if legacy_private_key:
        return legacy_private_key, None

    return None, None


def _validate_explicit_private_key(user: models.User, private_key: Optional[str]) -> Optional[str]:
    if not private_key:
        return None
    real_wallet_address = AuthService.get_user_wallet_address(user)
    if not verify_user_private_key(private_key, real_wallet_address, user.private_key_hash):
        raise HTTPException(status_code=403, detail="私钥校验失败")
    return normalize_private_key(private_key)


def _public_storage_key() -> str:
    return f"health-data-public::{settings.SECRET_KEY or 'health-data-default'}"


# 功能说明：组装用于链上存证和验真的原始载荷。
def _build_source_payload(
    file_type: str,
    *,
    data_content: Optional[str] = None,
    file_bytes: Optional[bytes] = None,
    file_mime_type: Optional[str] = None,
) -> str:
    if file_type in {"pdf", "word"}:
        if not file_bytes:
            return ""
        encoded = base64.b64encode(file_bytes).decode("utf-8")
        mime_type = file_mime_type or _default_mime_type(file_type) or "application/octet-stream"
        return f"data:{mime_type};base64,{encoded}"
    return data_content or ""


# 功能说明：计算健康数据载荷的 SHA-256 哈希。
def _hash_payload(payload: str) -> Optional[str]:
    if not payload:
        return None
    return "0x" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_chain_private_key(user: models.User, explicit_private_key: Optional[str]) -> Optional[str]:
    if explicit_private_key:
        return explicit_private_key
    if not user.encrypted_private_key:
        return None
    try:
        return normalize_private_key(AuthService.decrypt_private_key_from_storage(user.encrypted_private_key))
    except ValueError:
        return None


def _legacy_private_storage_key(user: Optional[models.User]) -> Optional[str]:
    if not user or not getattr(user, "private_key_hash", None):
        return None
    try:
        return normalize_private_key(user.private_key_hash)
    except ValueError:
        return None


def _ensure_user_encryption_public_key(user: models.User, private_key: Optional[str]) -> str:
    if user.encryption_public_key:
        return user.encryption_public_key
    if not private_key:
        raise HTTPException(status_code=400, detail="当前用户缺少可用的加密公钥")
    user.encryption_public_key = private_key_to_public_key(private_key)
    return user.encryption_public_key


# 功能说明：为私密记录生成 DEK 并用拥有者公钥封装。
def _build_owner_wrapped_dek(user: models.User, private_key: Optional[str]) -> tuple[bytes, str]:
    user_public_key = _ensure_user_encryption_public_key(user, private_key)
    dek = generate_data_encryption_key()
    wrapped = wrap_dek_for_public_key(dek, user_public_key)
    return dek, wrapped


def _resolve_grantee_public_key(grantee: models.User) -> Optional[str]:
    if grantee.encryption_public_key:
        return grantee.encryption_public_key
    if not grantee.encrypted_private_key:
        return None
    try:
        private_key = normalize_private_key(AuthService.decrypt_private_key_from_storage(grantee.encrypted_private_key))
        grantee.encryption_public_key = private_key_to_public_key(private_key)
        return grantee.encryption_public_key
    except ValueError:
        return None


# 功能说明：读取健康记录时解密真实内容。
def _resolve_record_values(
    record: models.HealthData,
    private_key: Optional[str] = None,
    *,
    source_is_public: Optional[bool] = None,
    current_user: Optional[models.User] = None,
    wrapped_dek: Optional[str] = None,
) -> tuple[Optional[str], Optional[bytes], bool]:
    is_public = record.is_public if source_is_public is None else source_is_public
    data_content = record.data_content
    file_bytes = record.pdf_data

    if not is_public:
        if not private_key:
            return None, None, True

        candidate_keys = [private_key]
        legacy_storage_key = _legacy_private_storage_key(current_user)
        if legacy_storage_key and legacy_storage_key not in candidate_keys:
            candidate_keys.append(legacy_storage_key)

        for candidate_key in candidate_keys:
            resolved_content = data_content
            resolved_file_bytes = file_bytes

            try:
                use_dek = bool(
                    (record.encryption_version or "").lower() == "dek_v1"
                    and (wrapped_dek or record.owner_encrypted_dek)
                )
                if use_dek:
                    resolved_dek = unwrap_dek_with_private_key((wrapped_dek or record.owner_encrypted_dek), candidate_key)
                    if record.encrypted_data_content:
                        resolved_content = decrypt_text_with_dek(record.encrypted_data_content, resolved_dek)
                    if record.encrypted_pdf_data:
                        resolved_file_bytes = decrypt_binary_with_dek(record.encrypted_pdf_data, resolved_dek)
                else:
                    if record.encrypted_data_content:
                        resolved_content = decrypt_text(record.encrypted_data_content, candidate_key)
                    if record.encrypted_pdf_data:
                        resolved_file_bytes = decrypt_binary(record.encrypted_pdf_data, candidate_key)
                return resolved_content, resolved_file_bytes, False
            except ValueError:
                continue

        return None, None, True

    storage_key = _public_storage_key()
    if record.encrypted_data_content or record.encrypted_pdf_data:
        try:
            if record.encrypted_data_content:
                data_content = decrypt_text(record.encrypted_data_content, storage_key)
            if record.encrypted_pdf_data:
                file_bytes = decrypt_binary(record.encrypted_pdf_data, storage_key)
        except ValueError:
            pass

    return data_content, file_bytes, False


# 功能说明：重新计算内容哈希并与链上存证比对。
def _verify_record_onchain(
    record: models.HealthData,
    *,
    data_content: Optional[str],
    file_bytes: Optional[bytes],
) -> tuple[Optional[str], Optional[bool], Optional[str]]:
    if not chain_service.enabled:
        return "service_unavailable", None, "区块链服务未启用，当前记录未执行链上验真"
    if not record.onchain_data_id:
        return "no_proof", None, "未生成链上存证"

    source_payload = _build_source_payload(
        record.file_type,
        data_content=data_content,
        file_bytes=file_bytes,
        file_mime_type=record.file_mime_type,
    )
    if not source_payload:
        if not record.is_public:
            return "locked", None, "私密数据未解锁或密文/密钥包可能已损坏，暂时无法完成链上校验"
        return "source_empty", None, "原始数据为空，无法完成链上校验"

    expected_hash = _hash_payload(source_payload)
    if not expected_hash:
        return "hash_failed", None, "数据摘要生成失败，无法完成链上校验"

    try:
        chain_record = chain_service.get_health_record(data_id_hex=record.onchain_data_id)
    except Exception as exc:  # noqa: BLE001
        return "query_failed", None, f"链上校验失败：{exc}"

    if not chain_record:
        return "record_missing", False, "未找到对应的链上记录"

    chain_hash = (chain_record.get("data_hash") or "").lower()
    if chain_hash == expected_hash.lower():
        return "verified", True, "链上哈希匹配，数据未被篡改"
    return "mismatch", False, "链上哈希与当前数据不一致，数据可能已被修改或尚未同步到链上"


def _serialize_record(
    record: models.HealthData,
    private_key: Optional[str] = None,
    current_user: Optional[models.User] = None,
    wrapped_dek: Optional[str] = None,
    include_file_data: bool = True,
    onchain_warning: Optional[str] = None,
) -> dict:
    data_content, file_bytes, requires_private_key = _resolve_record_values(
        record,
        private_key,
        current_user=current_user,
        wrapped_dek=wrapped_dek,
    )
    onchain_verification_status, onchain_verified, onchain_verification_message = _verify_record_onchain(
        record,
        data_content=data_content,
        file_bytes=file_bytes,
    )

    pdf_data_base64 = None
    if include_file_data and file_bytes:
        mime_type = record.file_mime_type or _default_mime_type(record.file_type) or "application/octet-stream"
        pdf_data_base64 = f"data:{mime_type};base64," + base64.b64encode(file_bytes).decode("utf-8")

    return {
        "id": record.id,
        "user_id": record.user_id,
        "data_title": record.data_title,
        "data_content": data_content,
        "file_type": record.file_type,
        "file_mime_type": record.file_mime_type,
        "pdf_size": record.pdf_size,
        "pdf_data_base64": pdf_data_base64,
        "is_public": record.is_public,
        "requires_private_key": requires_private_key,
        "onchain_verification_status": onchain_verification_status,
        "onchain_data_id": record.onchain_data_id,
        "onchain_tx_hash": record.onchain_tx_hash,
        "onchain_warning": onchain_warning,
        "onchain_verified": onchain_verified,
        "onchain_verification_message": onchain_verification_message,
        "recorded_at": record.created_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _serialize_grant(grant: models.HealthDataGrant, db: Session) -> dict:
    grantee_username = db.query(models.User.username).filter(models.User.id == grant.grantee_user_id).scalar()
    return {
        "id": grant.id,
        "record_id": grant.record_id,
        "owner_user_id": grant.owner_user_id,
        "grantee_user_id": grant.grantee_user_id,
        "grantee_username": grantee_username,
        "can_read": grant.can_read,
        "expires_at": grant.expires_at,
        "remark": grant.remark,
        "revoked_at": grant.revoked_at,
        "created_at": grant.created_at,
    }


def _ensure_record_dek_mode(
    record: models.HealthData,
    owner: models.User,
    owner_private_key: Optional[str],
) -> None:
    if record.is_public:
        return
    if record.owner_encrypted_dek and (record.encryption_version or "").lower() == "dek_v1":
        return
    if not owner_private_key:
        raise HTTPException(status_code=400, detail="当前记录仍为旧版加密，缺少私钥无法迁移")

    plain_content, plain_file_bytes, locked = _resolve_record_values(
        record,
        owner_private_key,
        source_is_public=False,
        current_user=owner,
    )
    if locked:
        raise HTTPException(status_code=400, detail="私钥校验失败，无法迁移记录加密方式")

    dek, owner_wrapped_dek = _build_owner_wrapped_dek(owner, owner_private_key)
    record.owner_encrypted_dek = owner_wrapped_dek
    record.encryption_version = "dek_v1"
    if record.file_type == "text":
        record.encrypted_data_content = encrypt_text_with_dek(plain_content or "", dek)
        record.encrypted_pdf_data = None
        record.pdf_data = None
    else:
        record.encrypted_pdf_data = encrypt_binary_with_dek(plain_file_bytes or b"", dek)
        record.encrypted_data_content = None
        record.data_content = None


# 功能说明：上传并创建健康数据，同时完成加密和存证。
@router.post("/records", response_model=schemas.HealthDataResponse)
async def create_health_record(
    health_data: schemas.HealthDataCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """创建健康记录"""
    recorded_at = health_data.recorded_at
    file_type = _normalized_file_type(health_data.file_type)
    file_bytes, file_size, file_mime_type = _decode_upload_data(file_type, health_data.pdf_data_base64)
    if "is_public" in health_data.model_fields_set:
        is_public = bool(health_data.is_public)
    else:
        is_public = _get_bool_system_setting(db, "default_health_data_public", False)
    effective_private_key, chain_private_key = _resolve_effective_private_key(current_user, health_data.private_key)
    if not is_public and not effective_private_key:
        raise HTTPException(status_code=400, detail="当前账号缺少可用私钥，无法保存私密健康数据")

    if file_type in {"pdf", "word"} and not file_bytes:
        raise HTTPException(status_code=400, detail="请上传文件")
    if file_type == "text" and not health_data.data_content:
        raise HTTPException(status_code=400, detail="文本健康数据不能为空")

    public_storage_key = _public_storage_key()
    record_dek = None
    owner_wrapped_dek = None
    encryption_version = "legacy"
    if not is_public:
        record_dek, owner_wrapped_dek = _build_owner_wrapped_dek(current_user, effective_private_key)
        encryption_version = "dek_v1"

    data_content = None
    encrypted_data_content = None
    plain_pdf_data = None
    encrypted_pdf_data = None

    if file_type == "text":
        if is_public:
            encrypted_data_content = encrypt_text(health_data.data_content or "", public_storage_key)
        elif record_dek:
            encrypted_data_content = encrypt_text_with_dek(health_data.data_content or "", record_dek)

    if file_type in {"pdf", "word"} and file_bytes:
        if is_public:
            encrypted_pdf_data = encrypt_binary(file_bytes, public_storage_key)
        elif record_dek:
            encrypted_pdf_data = encrypt_binary_with_dek(file_bytes, record_dek)

    record_kwargs = {}
    if recorded_at:
        record_kwargs["created_at"] = recorded_at

    db_record = models.HealthData(
        user_id=current_user.id,
        data_title=health_data.data_title,
        data_content=data_content,
        encrypted_data_content=encrypted_data_content,
        file_type=file_type,
        file_mime_type=file_mime_type,
        pdf_data=plain_pdf_data,
        encrypted_pdf_data=encrypted_pdf_data,
        owner_encrypted_dek=owner_wrapped_dek,
        encryption_version=encryption_version,
        pdf_size=file_size,
        is_public=is_public,
        **record_kwargs,
    )

    source_payload = _build_source_payload(
        file_type,
        data_content=health_data.data_content,
        file_bytes=file_bytes,
        file_mime_type=file_mime_type,
    )
    data_hash_hex = _hash_payload(source_payload)
    onchain_warning = None
    if not chain_private_key and source_payload and data_hash_hex:
        onchain_warning = "链上存证未执行：当前账号缺少可用私钥"
    elif chain_private_key and not chain_service.enabled and source_payload and data_hash_hex:
        onchain_warning = "链上存证未执行：区块链服务未启用或合约不可用"
    if chain_private_key and chain_service.enabled and source_payload and data_hash_hex:
        try:
            chain_result = await asyncio.to_thread(
                chain_service.store_health_data,
                owner_private_key=chain_private_key,
                data_hash_hex=data_hash_hex,
                encrypted_digest_source=source_payload,
                data_type=file_type,
            )
            if chain_result:
                db_record.onchain_tx_hash = chain_result.get("tx_hash")
                db_record.onchain_data_id = chain_result.get("data_id")
                if not db_record.onchain_data_id:
                    onchain_warning = "链上交易已发送，但未解析到链上数据ID，请检查合约事件"
            else:
                onchain_warning = "链上存证未执行：区块链服务返回空结果"
        except Exception as exc:  # noqa: BLE001
            onchain_warning = f"链上存证未执行：{exc}"

    db.add(db_record)
    AdminSystemService(db).log(
        level="INFO",
        module="health_records",
        action="create",
        message=(
            f"用户上传健康数据，类型：{file_type}，公开状态："
            f"{'公开' if is_public else '私密'}"
        ),
        operator_id=current_user.id,
        force=True,
    )
    if onchain_warning:
        AdminSystemService(db).log(
            level="WARN",
            module="health_records",
            action="onchain_warning",
            message=f"健康数据上链告警：{onchain_warning}，record_title={health_data.data_title or '-'}",
            operator_id=current_user.id,
        )
    db.commit()
    db.refresh(db_record)
    _invalidate_home_advice_if_needed(db, current_user, db_record.is_public)

    return _serialize_record(db_record, effective_private_key, current_user, onchain_warning=onchain_warning)


# 功能说明：查询当前用户的健康记录列表。
@router.get("/records", response_model=List[schemas.HealthDataResponse])
async def get_health_records(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    private_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取用户的健康数据记录"""
    query = db.query(models.HealthData).filter(models.HealthData.user_id == current_user.id)
    
    if start_date:
        query = query.filter(models.HealthData.created_at >= start_date)
    if end_date:
        query = query.filter(models.HealthData.created_at <= end_date)
    
    records = query.order_by(models.HealthData.created_at.desc()).offset(skip).limit(limit).all()
    AdminSystemService(db).log(
        level="INFO",
        module="health_records",
        action="view_list",
        message=f"User viewed health record list, count={len(records)}",
        operator_id=current_user.id,
        force=True,
    )
    db.commit()
    effective_private_key, _ = _resolve_effective_private_key(current_user, private_key)
    return [_serialize_record(item, effective_private_key, current_user) for item in records]


# 功能说明：查询单条健康数据详情。
@router.get("/records/{record_id}", response_model=schemas.HealthDataResponse)
async def get_health_record(
    record_id: int,
    private_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取单个健康数据记录"""
    record = db.query(models.HealthData).filter(
        models.HealthData.id == record_id,
        models.HealthData.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="健康数据记录不存在")
    
    AdminSystemService(db).log(
        level="INFO",
        module="health_records",
        action="view_detail",
        message=f"User viewed health record detail, record_id={record.id}",
        operator_id=current_user.id,
        force=True,
    )
    db.commit()
    effective_private_key, _ = _resolve_effective_private_key(current_user, private_key)
    return _serialize_record(record, effective_private_key, current_user)


# 功能说明：更新健康数据并同步链上存证。
@router.put("/records/{record_id}", response_model=schemas.HealthDataResponse)
async def update_health_record(
    record_id: int,
    health_data: schemas.HealthDataUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a health data record and keep on-chain proof in sync."""
    record = db.query(models.HealthData).filter(
        models.HealthData.id == record_id,
        models.HealthData.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="健康数据记录不存在")

    was_public = bool(record.is_public)
    previous_file_type = record.file_type
    update_data = health_data.model_dump(exclude_unset=True)
    input_private_key = update_data.pop("private_key", None)
    effective_private_key, chain_private_key = _resolve_effective_private_key(current_user, input_private_key)
    public_storage_key = _public_storage_key()

    if "data_title" in update_data:
        record.data_title = update_data["data_title"]
    if "recorded_at" in update_data and update_data["recorded_at"] is not None:
        record.created_at = update_data["recorded_at"]

    target_is_public = bool(update_data.get("is_public", record.is_public))
    target_file_type = _normalized_file_type(update_data.get("file_type", record.file_type))

    if not target_is_public and not effective_private_key:
        raise HTTPException(status_code=400, detail="当前账号缺少可用私钥，无法更新私密健康数据")

    existing_content, existing_file_bytes, was_locked = _resolve_record_values(
        record,
        effective_private_key,
        source_is_public=was_public,
        current_user=current_user,
    )

    payload_content = existing_content if previous_file_type == "text" else None
    payload_file_bytes = existing_file_bytes if previous_file_type in {"pdf", "word"} else None
    payload_file_mime_type = record.file_mime_type
    payload_file_size = record.pdf_size

    if target_file_type == "text":
        if "data_content" in update_data:
            payload_content = update_data["data_content"] or ""
        elif previous_file_type != "text":
            raise HTTPException(status_code=400, detail="更新为文本记录时必须提供 data_content")
        payload_file_bytes = None
        payload_file_mime_type = None
        payload_file_size = None
    else:
        if "pdf_data_base64" in update_data:
            decoded_file, decoded_size, detected_mime_type = _decode_upload_data(target_file_type, update_data["pdf_data_base64"])
            if not decoded_file:
                raise HTTPException(status_code=400, detail="上传文件内容无效")
            payload_file_bytes = decoded_file
            payload_file_size = decoded_size
            payload_file_mime_type = detected_mime_type
        elif previous_file_type != target_file_type:
            raise HTTPException(status_code=400, detail="切换文件类型时必须重新上传文件内容")
        payload_content = None

    encryption_rewrite_required = any(
        key in update_data for key in {"is_public", "file_type", "data_content", "pdf_data_base64"}
    )
    if encryption_rewrite_required and was_locked:
        raise HTTPException(status_code=400, detail="记录仍处于锁定状态，请提供正确私钥后重试")

    record.is_public = target_is_public
    record.file_type = target_file_type

    if encryption_rewrite_required:
        record.data_content = None
        record.pdf_data = None
        record.file_mime_type = payload_file_mime_type
        record.pdf_size = payload_file_size
        record.encrypted_data_content = None
        record.encrypted_pdf_data = None

        if target_is_public:
            record.owner_encrypted_dek = None
            record.encryption_version = "legacy"
            if target_file_type == "text":
                record.encrypted_data_content = encrypt_text(payload_content or "", public_storage_key)
            else:
                record.encrypted_pdf_data = encrypt_binary(payload_file_bytes or b"", public_storage_key)
        else:
            record_dek, owner_wrapped_dek = _build_owner_wrapped_dek(current_user, effective_private_key)
            record.owner_encrypted_dek = owner_wrapped_dek
            record.encryption_version = "dek_v1"
            if target_file_type == "text":
                record.encrypted_data_content = encrypt_text_with_dek(payload_content or "", record_dek)
            else:
                record.encrypted_pdf_data = encrypt_binary_with_dek(payload_file_bytes or b"", record_dek)

    resolved_content, resolved_file_bytes, _ = _resolve_record_values(
        record,
        effective_private_key,
        current_user=current_user,
    )
    source_payload = _build_source_payload(
        target_file_type,
        data_content=resolved_content,
        file_bytes=resolved_file_bytes,
        file_mime_type=record.file_mime_type,
    )
    data_hash_hex = _hash_payload(source_payload)
    onchain_warning = None
    if not chain_private_key and source_payload and data_hash_hex:
        onchain_warning = "链上存证未执行：当前账号缺少可用私钥"
    elif chain_private_key and not chain_service.enabled and source_payload and data_hash_hex:
        onchain_warning = "链上存证未执行：区块链服务未启用或合约不可用"

    if chain_private_key and chain_service.enabled and source_payload and data_hash_hex:
        try:
            if record.onchain_data_id:
                chain_result = await asyncio.to_thread(
                    chain_service.update_health_data,
                    owner_private_key=chain_private_key,
                    data_id_hex=record.onchain_data_id,
                    data_hash_hex=data_hash_hex,
                    encrypted_digest_source=source_payload,
                )
            else:
                chain_result = await asyncio.to_thread(
                    chain_service.store_health_data,
                    owner_private_key=chain_private_key,
                    data_hash_hex=data_hash_hex,
                    encrypted_digest_source=source_payload,
                    data_type=target_file_type,
                )
            if chain_result:
                record.onchain_tx_hash = chain_result.get("tx_hash")
                record.onchain_data_id = chain_result.get("data_id") or record.onchain_data_id
                if not record.onchain_data_id:
                    onchain_warning = "链上交易已发送，但未解析到链上数据ID，请检查合约事件"
            else:
                onchain_warning = "链上存证未执行：区块链服务返回空结果"
        except Exception as exc:  # noqa: BLE001
            onchain_warning = f"链上存证未执行：{exc}"

    AdminSystemService(db).log(
        level="INFO",
        module="health_records",
        action="update",
        message=(
            f"用户更新健康数据，记录ID：{record.id}，类型：{target_file_type}，公开状态："
            f"{'公开' if record.is_public else '私密'}"
        ),
        operator_id=current_user.id,
    )
    if onchain_warning:
        AdminSystemService(db).log(
            level="WARN",
            module="health_records",
            action="onchain_warning",
            message=f"健康数据上链告警：{onchain_warning}，record_id={record.id}",
            operator_id=current_user.id,
        )
    db.commit()
    db.refresh(record)
    _invalidate_home_advice_if_needed(db, current_user, was_public or record.is_public)
    return _serialize_record(record, effective_private_key, current_user, onchain_warning=onchain_warning)


@router.get("/public/records", response_model=List[schemas.HealthDataResponse])
async def get_public_health_records(
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    records = (
        db.query(models.HealthData)
        .filter(models.HealthData.is_public.is_(True))
        .order_by(models.HealthData.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_serialize_record(item, include_file_data=False) for item in records]


@router.get("/public/records/{record_id}", response_model=schemas.HealthDataResponse)
async def get_public_health_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.HealthData).filter(
        models.HealthData.id == record_id,
        models.HealthData.is_public.is_(True),
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="公开健康数据不存在")
    return _serialize_record(record)


@router.get("/grantable-users", response_model=List[schemas.HealthDataGrantableUser])
async def get_grantable_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    users = (
        db.query(models.User)
        .filter(models.User.is_active.is_(True), models.User.id != current_user.id)
        .order_by(models.User.role.asc(), models.User.id.asc())
        .all()
    )
    return [{"id": item.id, "username": item.username, "role": item.role} for item in users]


@router.get("/records/{record_id}/grants", response_model=List[schemas.HealthDataGrantResponse])
async def get_record_grants(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = db.query(models.HealthData).filter(
        models.HealthData.id == record_id,
        models.HealthData.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="健康数据记录不存在")

    grants = (
        db.query(models.HealthDataGrant)
        .filter(models.HealthDataGrant.record_id == record.id)
        .order_by(models.HealthDataGrant.created_at.desc())
        .all()
    )
    return [_serialize_grant(item, db) for item in grants]


# 功能说明：为私密健康数据创建授权。
@router.post("/records/{record_id}/grants", response_model=schemas.HealthDataGrantResponse)
async def create_record_grant(
    record_id: int,
    payload: schemas.HealthDataGrantCreate,
    private_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    record = db.query(models.HealthData).filter(
        models.HealthData.id == record_id,
        models.HealthData.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="健康数据记录不存在")
    if record.is_public:
        raise HTTPException(status_code=400, detail="公开记录无需授权")
    if payload.grantee_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能给自己授权")

    grantee = db.query(models.User).filter(models.User.id == payload.grantee_user_id).first()
    if not grantee or not grantee.is_active:
        raise HTTPException(status_code=404, detail="被授权用户不存在或不可用")

    effective_private_key, _ = _resolve_effective_private_key(current_user, private_key)
    if not effective_private_key:
        raise HTTPException(status_code=400, detail="当前账号缺少可用私钥，无法完成授权")

    _ensure_record_dek_mode(record, current_user, effective_private_key)
    grantee_public_key = _resolve_grantee_public_key(grantee)
    if not grantee_public_key:
        raise HTTPException(status_code=400, detail="被授权用户缺少可用加密公钥")
    wrapped_for_grantee = rewrap_dek_for_recipient(
        record.owner_encrypted_dek,
        effective_private_key,
        grantee_public_key,
    )

    now = datetime.utcnow()
    expires_at = now + timedelta(days=int(payload.expires_days or 30))
    grant = (
        db.query(models.HealthDataGrant)
        .filter(
            models.HealthDataGrant.record_id == record.id,
            models.HealthDataGrant.owner_user_id == current_user.id,
            models.HealthDataGrant.grantee_user_id == grantee.id,
            models.HealthDataGrant.revoked_at.is_(None),
        )
        .order_by(models.HealthDataGrant.id.desc())
        .first()
    )
    if grant:
        grant.wrapped_dek = wrapped_for_grantee
        grant.can_read = True
        grant.expires_at = expires_at
        grant.remark = payload.remark
    else:
        grant = models.HealthDataGrant(
            record_id=record.id,
            owner_user_id=current_user.id,
            grantee_user_id=grantee.id,
            wrapped_dek=wrapped_for_grantee,
            can_read=True,
            expires_at=expires_at,
            remark=payload.remark,
        )
        db.add(grant)

    db.commit()
    db.refresh(grant)
    return _serialize_grant(grant, db)


@router.delete("/grants/{grant_id}")
async def revoke_record_grant(
    grant_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    grant = db.query(models.HealthDataGrant).filter(models.HealthDataGrant.id == grant_id).first()
    if not grant:
        raise HTTPException(status_code=404, detail="授权记录不存在")
    if grant.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权撤销该授权")
    if grant.revoked_at is None:
        grant.revoked_at = datetime.utcnow()
        db.commit()
    return {"message": "撤销成功"}


# 功能说明：查询授权给当前用户的私密数据。
@router.get("/shared/records", response_model=List[schemas.HealthDataResponse])
async def get_shared_health_records(
    skip: int = 0,
    limit: int = 100,
    private_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    effective_private_key, _ = _resolve_effective_private_key(current_user, private_key)
    if not effective_private_key:
        return []

    now = datetime.utcnow()
    grants = (
        db.query(models.HealthDataGrant)
        .join(models.HealthData, models.HealthData.id == models.HealthDataGrant.record_id)
        .filter(
            models.HealthDataGrant.grantee_user_id == current_user.id,
            models.HealthDataGrant.can_read.is_(True),
            models.HealthDataGrant.revoked_at.is_(None),
            models.HealthData.is_public.is_(False),
            or_(models.HealthDataGrant.expires_at.is_(None), models.HealthDataGrant.expires_at > now),
        )
        .order_by(models.HealthDataGrant.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    output: list[dict] = []
    for grant in grants:
        record = db.query(models.HealthData).filter(models.HealthData.id == grant.record_id).first()
        if not record:
            continue
        output.append(
            _serialize_record(
                record,
                effective_private_key,
                current_user=current_user,
                wrapped_dek=grant.wrapped_dek,
            )
        )
    return output


@router.get("/shared/records/{record_id}", response_model=schemas.HealthDataResponse)
async def get_shared_health_record(
    record_id: int,
    private_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    effective_private_key, _ = _resolve_effective_private_key(current_user, private_key)
    if not effective_private_key:
        raise HTTPException(status_code=403, detail="当前账号缺少可用私钥，无法查看共享私密数据")

    now = datetime.utcnow()
    grant = (
        db.query(models.HealthDataGrant)
        .filter(
            models.HealthDataGrant.record_id == record_id,
            models.HealthDataGrant.grantee_user_id == current_user.id,
            models.HealthDataGrant.can_read.is_(True),
            models.HealthDataGrant.revoked_at.is_(None),
            or_(models.HealthDataGrant.expires_at.is_(None), models.HealthDataGrant.expires_at > now),
        )
        .order_by(models.HealthDataGrant.created_at.desc())
        .first()
    )
    if not grant:
        raise HTTPException(status_code=404, detail="未找到可用授权")

    record = db.query(models.HealthData).filter(
        models.HealthData.id == record_id,
        models.HealthData.is_public.is_(False),
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="共享记录不存在")

    return _serialize_record(
        record,
        effective_private_key,
        current_user=current_user,
        wrapped_dek=grant.wrapped_dek,
    )


@router.delete("/records/{record_id}")
async def delete_health_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """删除健康数据记录"""
    record = db.query(models.HealthData).filter(
        models.HealthData.id == record_id,
        models.HealthData.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="健康数据记录不存在")

    was_public = bool(record.is_public)
    AdminSystemService(db).log(
        level="INFO",
        module="health_records",
        action="delete",
        message=(
            f"用户删除健康数据，记录ID：{record.id}，类型：{record.file_type}，公开状态："
            f"{'公开' if record.is_public else '私密'}"
        ),
        operator_id=current_user.id,
    )
    db.delete(record)
    db.commit()
    _invalidate_home_advice_if_needed(db, current_user, was_public)
    return {"message": "健康数据记录已删除"}


@router.get("/summary")
async def get_health_summary(
    private_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取健康数据摘要统计"""
    effective_private_key, _ = _resolve_effective_private_key(current_user, private_key)

    records = (
        db.query(models.HealthData)
        .filter(models.HealthData.user_id == current_user.id)
        .order_by(models.HealthData.created_at.desc())
        .all()
    )

    if not records:
        return {
            "total_records": 0,
            "latest_record": None,
            "average_weight": None,
            "average_heart_rate": None,
            "records_this_month": 0,
        }

    total_records = len(records)
    latest_record = records[0]

    weights = []
    heart_rates = []
    for item in records:
        content, _, _ = _resolve_record_values(item, effective_private_key, current_user=current_user)
        metrics = _extract_metrics(content)
        if metrics.get("weight") is not None:
            weights.append(metrics.get("weight"))
        if metrics.get("heart_rate") is not None:
            heart_rates.append(metrics.get("heart_rate"))

    summary = {
        "total_records": total_records,
        "latest_record": latest_record.created_at if latest_record else None,
        "average_weight": sum(weights) / len(weights) if weights else None,
        "average_heart_rate": sum(heart_rates) / len(heart_rates) if heart_rates else None,
        "records_this_month": len([
            r for r in records
            if r.created_at.month == datetime.now().month and r.created_at.year == datetime.now().year
        ]),
    }

    return summary


@router.post("/analyze")
async def analyze_health_data(
    analysis_request: schemas.HealthAnalysisRequest,
    private_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """分析健康数据并提供建议"""
    effective_private_key, _ = _resolve_effective_private_key(current_user, private_key)

    query = db.query(models.HealthData).filter(models.HealthData.user_id == current_user.id)

    if analysis_request.start_date:
        query = query.filter(models.HealthData.created_at >= analysis_request.start_date)
    if analysis_request.end_date:
        query = query.filter(models.HealthData.created_at <= analysis_request.end_date)

    records = query.order_by(models.HealthData.created_at.desc()).all()

    if not records:
        return {"analysis": "暂无数据可供分析", "recommendations": []}

    recommendations = []

    latest_record = records[0]
    latest_content, _, _ = _resolve_record_values(latest_record, effective_private_key, current_user=current_user)
    metrics = _extract_metrics(latest_content)
    systolic = metrics.get("blood_pressure_systolic")
    diastolic = metrics.get("blood_pressure_diastolic")
    if systolic and diastolic:
        if systolic > 140 or diastolic > 90:
            recommendations.append("您的血压偏高，建议咨询医生并注意低盐饮食")
        elif systolic < 90 or diastolic < 60:
            recommendations.append("您的血压偏低，建议适当增加运动和营养")
        else:
            recommendations.append("您的血压正常，请继续保持")

    heart_rate = metrics.get("heart_rate")
    if heart_rate:
        if heart_rate > 100:
            recommendations.append("您的心率偏快，建议放松心情，避免过度劳累")
        elif heart_rate < 60:
            recommendations.append("您的心率偏慢，如果您不是运动员，建议咨询医生")
        else:
            recommendations.append("您的心率正常，请继续保持")

    blood_sugar = metrics.get("blood_sugar")
    if blood_sugar:
        if blood_sugar > 6.1:
            recommendations.append("您的血糖偏高，建议控制糖分摄入，增加运动")
        elif blood_sugar < 3.9:
            recommendations.append("您的血糖偏低，建议规律饮食，避免低血糖")
        else:
            recommendations.append("您的血糖正常，请继续保持")

    return {
        "analysis": f"基于您最近的{len(records)}条健康数据记录进行分析",
        "recommendations": recommendations,
        "data_points": len(records),
        "analysis_date": datetime.now().isoformat(),
    }
