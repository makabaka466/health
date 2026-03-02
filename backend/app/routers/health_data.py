import base64
import json
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.routers.auth import get_current_user


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


def _serialize_record(record: models.HealthData) -> dict:
    pdf_data_base64 = None
    if record.pdf_data:
        pdf_data_base64 = "data:application/pdf;base64," + base64.b64encode(record.pdf_data).decode("utf-8")

    return {
        "id": record.id,
        "user_id": record.user_id,
        "data_title": record.data_title,
        "data_content": record.data_content,
        "file_type": record.file_type,
        "pdf_size": record.pdf_size,
        "pdf_data_base64": pdf_data_base64,
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
    if file_type == "pdf" and not pdf_data:
        raise HTTPException(status_code=400, detail="请上传 PDF 文件")
    if file_type == "text" and not health_data.data_content:
        raise HTTPException(status_code=400, detail="文本健康数据不能为空")

    db_record = models.HealthData(
        user_id=current_user.id,
        data_title=health_data.data_title,
        data_content=health_data.data_content,
        file_type=file_type,
        pdf_data=pdf_data,
        pdf_size=pdf_size,
    )
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return _serialize_record(db_record)


@router.get("/records", response_model=List[schemas.HealthDataResponse])
async def get_health_records(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
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
    return [_serialize_record(item) for item in records]


@router.get("/records/{record_id}", response_model=schemas.HealthDataResponse)
async def get_health_record(
    record_id: int,
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
    
    return _serialize_record(record)


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
    
    update_data = health_data.dict(exclude_unset=True)
    if "file_type" in update_data:
        update_data["file_type"] = "pdf" if update_data["file_type"] == "pdf" else "text"

    current_type = update_data.get("file_type", record.file_type)
    pdf_input = update_data.pop("pdf_data_base64", None)

    if current_type == "pdf":
        candidate_pdf = pdf_input if pdf_input is not None else (
            "data:application/pdf;base64," + base64.b64encode(record.pdf_data).decode("utf-8")
            if record.pdf_data
            else None
        )
        decoded, size, _ = _decode_pdf_data(candidate_pdf)
        if not decoded:
            raise HTTPException(status_code=400, detail="请上传 PDF 文件")
        update_data["pdf_data"] = decoded
        update_data["pdf_size"] = size
    else:
        update_data["pdf_data"] = None
        update_data["pdf_size"] = None

    for field, value in update_data.items():
        setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取健康数据摘要统计"""
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
        metrics = _extract_metrics(item.data_content)
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
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """分析健康数据并提供建议"""
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
    metrics = _extract_metrics(latest_record.data_content)
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
