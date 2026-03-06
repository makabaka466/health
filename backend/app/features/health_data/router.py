import base64
import hashlib
import json
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.features.auth.dependencies import get_current_user
from app.features.blockchain.service import chain_service
from app.features.blockchain.encryption import (
    decrypt_binary,
    decrypt_text,
    encrypt_binary,
    encrypt_text,
    normalize_private_key,
    verify_user_private_key,
)


router = APIRouter()


def _decode_pdf_data(pdf_data_base64: Optional[str]) -> tuple[Optional[bytes], Optional[int], Optional[str]]:
    if not pdf_data_base64:
        return None, None, None

    raw_value = pdf_data_base64.strip()
    if not raw_value:
        return None, None, None

    if "," in raw_value:
        prefix, encoded_value = raw_value.split(",", 1)
        if "application/pdf" not in prefix and "application/octet-stream" not in prefix:
            raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")
    else:
        encoded_value = raw_value

    try:
        decoded = base64.b64decode(encoded_value, validate=True)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="PDF 文件内容非法") from exc

    if not decoded.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")

    if len(decoded) > 6 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="PDF 文件过大，请压缩后再上传")

    return decoded, len(decoded), f"data:application/pdf;base64,{encoded_value}"


def _extract_metrics(content: Optional[str]) -> dict:
    if not content:
        return {}
    try:
        payload = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return {}
    return payload.get("metrics", {}) if isinstance(payload, dict) else {}


def _resolve_effective_private_key(user: models.User, private_key: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    if private_key:
        if not verify_user_private_key(private_key, user.wallet_address, user.private_key_hash):
            raise HTTPException(status_code=403, detail="私钥校验失败")
        normalized_key = normalize_private_key(private_key)
        return normalized_key, normalized_key

    if user.private_key_hash:
        # 当前用户身份已通过 JWT 鉴权时，允许自动使用其密钥哈希派生的内部密钥处理私密数据。
        return normalize_private_key(user.private_key_hash), None

    return None, None


def _serialize_record(record: models.HealthData, private_key: Optional[str] = None) -> dict:
    requires_private_key = bool(not record.is_public and (record.encrypted_data_content or record.encrypted_pdf_data))
    data_content = record.data_content
    pdf_bytes = record.pdf_data

    if requires_private_key and private_key:
        try:
            if record.encrypted_data_content:
                data_content = decrypt_text(record.encrypted_data_content, private_key)
            if record.encrypted_pdf_data:
                pdf_bytes = decrypt_binary(record.encrypted_pdf_data, private_key)
            requires_private_key = False
        except ValueError:
            # 历史数据可能由原始私钥加密，若自动密钥无法解开则仍提示需要显式私钥。
            requires_private_key = True

    pdf_data_base64 = None
    if pdf_bytes:
        pdf_data_base64 = "data:application/pdf;base64," + base64.b64encode(pdf_bytes).decode("utf-8")

    return {
        "id": record.id,
        "user_id": record.user_id,
        "data_title": record.data_title,
        "data_content": data_content,
        "file_type": record.file_type,
        "pdf_size": record.pdf_size,
        "pdf_data_base64": pdf_data_base64,
        "is_public": record.is_public,
        "requires_private_key": requires_private_key,
        "onchain_tx_hash": record.onchain_tx_hash,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


@router.post("/records", response_model=schemas.HealthDataResponse)
async def create_health_record(
    health_data: schemas.HealthDataCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """创建健康数据记录"""
    file_type = "pdf" if health_data.file_type == "pdf" else "text"
    pdf_data, pdf_size, _ = _decode_pdf_data(health_data.pdf_data_base64 if file_type == "pdf" else None)
    is_public = bool(health_data.is_public)
    private_key, explicit_private_key = _resolve_effective_private_key(current_user, health_data.private_key)

    if not is_public and not private_key:
        raise HTTPException(status_code=400, detail="私密健康数据必须提供 private_key")

    if file_type == "pdf" and not pdf_data:
        raise HTTPException(status_code=400, detail="请上传 PDF 文件")
    if file_type == "text" and not health_data.data_content:
        raise HTTPException(status_code=400, detail="文本健康数据不能为空")

    data_content = health_data.data_content
    encrypted_data_content = None
    plain_pdf_data = pdf_data
    encrypted_pdf_data = None

    if not is_public and private_key:
        encrypted_data_content = encrypt_text(health_data.data_content or "", private_key)
        data_content = None
        if pdf_data:
            encrypted_pdf_data = encrypt_binary(pdf_data, private_key)
            plain_pdf_data = None

    db_record = models.HealthData(
        user_id=current_user.id,
        data_title=health_data.data_title,
        data_content=data_content,
        encrypted_data_content=encrypted_data_content,
        file_type=file_type,
        pdf_data=plain_pdf_data,
        encrypted_pdf_data=encrypted_pdf_data,
        pdf_size=pdf_size,
        is_public=is_public,
    )

    if explicit_private_key:
        source_payload = health_data.data_content or (health_data.pdf_data_base64 or "")
        if source_payload:
            data_hash_hex = "0x" + hashlib.sha256(source_payload.encode("utf-8")).hexdigest()
            try:
                chain_result = chain_service.store_health_data(
                    owner_private_key=explicit_private_key,
                    data_hash_hex=data_hash_hex,
                    encrypted_digest_source=source_payload,
                    data_type=file_type,
                )
                if chain_result:
                    db_record.onchain_tx_hash = chain_result.get("tx_hash")
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=400, detail=f"上链失败：{exc}") from exc
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return _serialize_record(db_record, private_key)


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
    validated_key, _ = _resolve_effective_private_key(current_user, private_key)
    return [_serialize_record(item, validated_key) for item in records]


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
    
    validated_key, _ = _resolve_effective_private_key(current_user, private_key)
    return _serialize_record(record, validated_key)


@router.put("/records/{record_id}", response_model=schemas.HealthDataResponse)
async def update_health_record(
    record_id: int,
    health_data: schemas.HealthDataUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """更新健康数据记录"""
    record = db.query(models.HealthData).filter(
        models.HealthData.id == record_id,
        models.HealthData.user_id == current_user.id
    ).first()
    
    if not record:
        raise HTTPException(status_code=404, detail="健康数据记录不存在")

    update_data = health_data.model_dump(exclude_unset=True)
    private_key, explicit_private_key = _resolve_effective_private_key(current_user, update_data.pop("private_key", None))

    if "data_title" in update_data:
        record.data_title = update_data["data_title"]

    if "is_public" in update_data:
        record.is_public = bool(update_data["is_public"])

    target_file_type = "pdf" if update_data.get("file_type", record.file_type) == "pdf" else "text"
    record.file_type = target_file_type

    if not record.is_public and not private_key:
        raise HTTPException(status_code=400, detail="更新私密健康数据需要提供 private_key")

    if target_file_type == "text" and "data_content" in update_data:
        if record.is_public:
            record.data_content = update_data["data_content"]
            record.encrypted_data_content = None
        else:
            record.data_content = None
            record.encrypted_data_content = encrypt_text(update_data["data_content"] or "", private_key)

    if target_file_type == "pdf" and "pdf_data_base64" in update_data:
        decoded_pdf, decoded_size, _ = _decode_pdf_data(update_data["pdf_data_base64"])
        if not decoded_pdf:
            raise HTTPException(status_code=400, detail="请上传 PDF 文件")

        record.pdf_size = decoded_size
        if record.is_public:
            record.pdf_data = decoded_pdf
            record.encrypted_pdf_data = None
        else:
            record.pdf_data = None
            record.encrypted_pdf_data = encrypt_binary(decoded_pdf, private_key)

    if explicit_private_key and ("data_content" in update_data or "pdf_data_base64" in update_data):
        source_payload = update_data.get("data_content") or update_data.get("pdf_data_base64") or ""
        if source_payload:
            data_hash_hex = "0x" + hashlib.sha256(source_payload.encode("utf-8")).hexdigest()
            try:
                chain_result = chain_service.store_health_data(
                    owner_private_key=explicit_private_key,
                    data_hash_hex=data_hash_hex,
                    encrypted_digest_source=source_payload,
                    data_type=target_file_type,
                )
                if chain_result:
                    record.onchain_tx_hash = chain_result.get("tx_hash")
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=400, detail=f"上链失败：{exc}") from exc
    
    db.commit()
    db.refresh(record)
    return _serialize_record(record, private_key)


@router.get("/public/records", response_model=List[schemas.HealthDataResponse])
async def get_public_health_records(
    skip: int = 0,
    limit: int = 100,
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
    return [_serialize_record(item) for item in records]


@router.get("/public/records/{record_id}", response_model=schemas.HealthDataResponse)
async def get_public_health_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.HealthData).filter(
        models.HealthData.id == record_id,
        models.HealthData.is_public.is_(True),
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="公开健康数据不存在")
    return _serialize_record(record)


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
    
    db.delete(record)
    db.commit()
    return {"message": "健康数据记录已删除"}


@router.get("/summary")
async def get_health_summary(
    private_key: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取健康数据摘要统计"""
    validated_key, _ = _resolve_effective_private_key(current_user, private_key)

    records = db.query(models.HealthData).filter(
        models.HealthData.user_id == current_user.id
    ).all()
    
    if not records:
        return {
            "total_records": 0,
            "latest_record": None,
            "average_weight": None,
            "average_heart_rate": None,
            "records_this_month": 0,
        }
    
    # 计算统计数据
    total_records = len(records)
    latest_record = records[0] if records else None
    
    # 计算平均值
    weights = []
    heart_rates = []
    for item in records:
        content = item.data_content
        if not item.is_public and item.encrypted_data_content and validated_key:
            try:
                content = decrypt_text(item.encrypted_data_content, validated_key)
            except ValueError:
                content = item.data_content
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
        "records_this_month": len([r for r in records 
                                 if r.created_at.month == datetime.now().month 
                                 and r.created_at.year == datetime.now().year])
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
    validated_key, _ = _resolve_effective_private_key(current_user, private_key)

    # 获取指定时间范围的数据
    query = db.query(models.HealthData).filter(models.HealthData.user_id == current_user.id)
    
    if analysis_request.start_date:
        query = query.filter(models.HealthData.created_at >= analysis_request.start_date)
    if analysis_request.end_date:
        query = query.filter(models.HealthData.created_at <= analysis_request.end_date)
    
    records = query.order_by(models.HealthData.created_at.desc()).all()
    
    if not records:
        return {"analysis": "暂无数据可供分析", "recommendations": []}
    
    # 简单的健康分析逻辑
    recommendations = []
    
    # 分析血压
    latest_record = records[0]
    latest_content = latest_record.data_content
    if not latest_record.is_public and latest_record.encrypted_data_content and validated_key:
        try:
            latest_content = decrypt_text(latest_record.encrypted_data_content, validated_key)
        except ValueError:
            latest_content = latest_record.data_content
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
    
    # 分析心率
    heart_rate = metrics.get("heart_rate")
    if heart_rate:
        if heart_rate > 100:
            recommendations.append("您的心率偏快，建议放松心情，避免过度劳累")
        elif heart_rate < 60:
            recommendations.append("您的心率偏慢，如果您不是运动员，建议咨询医生")
        else:
            recommendations.append("您的心率正常，请继续保持")
    
    # 分析血糖
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
        "analysis_date": datetime.now().isoformat()
    }
