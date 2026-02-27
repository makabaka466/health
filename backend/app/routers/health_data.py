from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date

from app.database import get_db
from app import models, schemas
from app.routers.auth import get_current_user


router = APIRouter()


def _normalize_pdf_file(file_value: Optional[str]) -> Optional[str]:
    if not file_value:
        return None

    file_value = file_value.strip()
    if not file_value:
        return None

    allowed_prefixes = (
        "data:application/pdf;base64,",
        "data:application/octet-stream;base64,",
    )
    if not file_value.startswith(allowed_prefixes):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")

    # 避免单条记录文件过大导致数据库膨胀（约 6MB base64）
    if len(file_value) > 8_000_000:
        raise HTTPException(status_code=400, detail="PDF 文件过大，请压缩后再上传")

    return file_value


@router.post("/records", response_model=schemas.HealthDataResponse)
async def create_health_record(
    health_data: schemas.HealthDataCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """创建健康数据记录"""
    normalized_file = _normalize_pdf_file(health_data.health_data_file)
    record_type = "pdf" if normalized_file else "manual"

    db_record = models.HealthData(
        user_id=current_user.id,
        weight=health_data.weight,
        height=health_data.height,
        blood_pressure_systolic=health_data.blood_pressure_systolic,
        blood_pressure_diastolic=health_data.blood_pressure_diastolic,
        heart_rate=health_data.heart_rate,
        blood_sugar=health_data.blood_sugar,
        record_type=record_type,
        is_private=True if record_type == "pdf" else health_data.is_private,
        health_data_file_name=health_data.health_data_file_name,
        health_data_file=normalized_file,
        recorded_at=health_data.recorded_at or datetime.utcnow()
    )
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return db_record


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
        query = query.filter(models.HealthData.recorded_at >= start_date)
    if end_date:
        query = query.filter(models.HealthData.recorded_at <= end_date)
    
    records = query.order_by(models.HealthData.recorded_at.desc()).offset(skip).limit(limit).all()
    return records


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
    
    return record


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
    
    # 更新字段
    update_data = health_data.dict(exclude_unset=True)
    if "health_data_file" in update_data:
        update_data["health_data_file"] = _normalize_pdf_file(update_data["health_data_file"])

    has_file = bool(update_data.get("health_data_file", record.health_data_file))
    update_data["record_type"] = "pdf" if has_file else "manual"
    if update_data["record_type"] == "pdf" and "is_private" not in update_data:
        update_data["is_private"] = True

    for field, value in update_data.items():
        setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
    return record


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
        return {"message": "暂无健康数据"}
    
    # 计算统计数据
    total_records = len(records)
    latest_record = records[-1] if records else None
    
    # 计算平均值
    weights = [r.weight for r in records if r.weight]
    heart_rates = [r.heart_rate for r in records if r.heart_rate]
    
    summary = {
        "total_records": total_records,
        "latest_record": latest_record.recorded_at if latest_record else None,
        "average_weight": sum(weights) / len(weights) if weights else None,
        "average_heart_rate": sum(heart_rates) / len(heart_rates) if heart_rates else None,
        "records_this_month": len([r for r in records 
                                 if r.recorded_at.month == datetime.now().month 
                                 and r.recorded_at.year == datetime.now().year])
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
        query = query.filter(models.HealthData.recorded_at >= analysis_request.start_date)
    if analysis_request.end_date:
        query = query.filter(models.HealthData.recorded_at <= analysis_request.end_date)
    
    records = query.order_by(models.HealthData.recorded_at.desc()).all()
    
    if not records:
        return {"analysis": "暂无数据可供分析", "recommendations": []}
    
    # 简单的健康分析逻辑
    recommendations = []
    
    # 分析血压
    latest_record = records[0]
    if latest_record.blood_pressure_systolic and latest_record.blood_pressure_diastolic:
        systolic = latest_record.blood_pressure_systolic
        diastolic = latest_record.blood_pressure_diastolic
        
        if systolic > 140 or diastolic > 90:
            recommendations.append("您的血压偏高，建议咨询医生并注意低盐饮食")
        elif systolic < 90 or diastolic < 60:
            recommendations.append("您的血压偏低，建议适当增加运动和营养")
        else:
            recommendations.append("您的血压正常，请继续保持")
    
    # 分析心率
    if latest_record.heart_rate:
        if latest_record.heart_rate > 100:
            recommendations.append("您的心率偏快，建议放松心情，避免过度劳累")
        elif latest_record.heart_rate < 60:
            recommendations.append("您的心率偏慢，如果您不是运动员，建议咨询医生")
        else:
            recommendations.append("您的心率正常，请继续保持")
    
    # 分析血糖
    if latest_record.blood_sugar:
        if latest_record.blood_sugar > 6.1:
            recommendations.append("您的血糖偏高，建议控制糖分摄入，增加运动")
        elif latest_record.blood_sugar < 3.9:
            recommendations.append("您的血糖偏低，建议规律饮食，避免低血糖")
        else:
            recommendations.append("您的血糖正常，请继续保持")
    
    return {
        "analysis": f"基于您最近的{len(records)}条健康数据记录进行分析",
        "recommendations": recommendations,
        "data_points": len(records),
        "analysis_date": datetime.now().isoformat()
    }
