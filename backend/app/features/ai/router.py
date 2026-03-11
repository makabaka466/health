from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.database import get_db
from app import models, schemas
from app.features.auth.dependencies import get_current_user


router = APIRouter()


def _extract_metrics_from_record(record: models.HealthData) -> dict:
    if not record.data_content:
        return {}
    try:
        payload = json.loads(record.data_content)
    except (TypeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    metrics = payload.get("metrics")
    return metrics if isinstance(metrics, dict) else {}


def _load_public_health_records(db: Session, user_id: int, limit: int = 10) -> list[models.HealthData]:
    return (
        db.query(models.HealthData)
        .filter(
            models.HealthData.user_id == user_id,
            models.HealthData.is_public.is_(True),
            models.HealthData.data_content.isnot(None),
        )
        .order_by(models.HealthData.created_at.desc())
        .limit(limit)
        .all()
    )


def _build_public_health_context(records: list[models.HealthData]) -> tuple[str, list[str]]:
    if not records:
        return "", []

    latest = records[0]
    metrics = _extract_metrics_from_record(latest)
    highlights: list[str] = []

    for key, label in [
        ("blood_pressure_systolic", "收缩压"),
        ("blood_pressure_diastolic", "舒张压"),
        ("heart_rate", "心率"),
        ("blood_sugar", "血糖"),
        ("weight", "体重"),
    ]:
        if metrics.get(key) is not None:
            highlights.append(f"{label}:{metrics.get(key)}")

    summary = f"已读取用户最近{len(records)}条公开健康记录。"
    if highlights:
        summary += " 最近一次关键指标：" + "，".join(highlights) + "。"
    return summary, highlights


def _retrieve_rag_context(db: Session, question: str, limit: int = 3) -> tuple[str, list[str]]:
    keywords = [token.strip() for token in question.split() if token.strip()]
    if not keywords:
        keywords = [question.strip()]

    docs_query = db.query(models.RagKnowledgeDocument).filter(models.RagKnowledgeDocument.is_active.is_(True))
    for word in keywords[:5]:
        like = f"%{word}%"
        docs_query = docs_query.filter(
            or_(
                models.RagKnowledgeDocument.title.ilike(like),
                models.RagKnowledgeDocument.content.ilike(like),
                models.RagKnowledgeDocument.category.ilike(like),
            )
        )
    rag_docs = docs_query.order_by(models.RagKnowledgeDocument.updated_at.desc()).limit(limit).all()

    article_query = db.query(models.HealthArticle)
    for word in keywords[:3]:
        like = f"%{word}%"
        article_query = article_query.filter(
            or_(
                models.HealthArticle.title.ilike(like),
                models.HealthArticle.summary.ilike(like),
                models.HealthArticle.content.ilike(like),
            )
        )
    rag_articles = article_query.order_by(models.HealthArticle.view_count.desc()).limit(max(1, limit - len(rag_docs))).all()

    snippets: list[str] = []
    references: list[str] = []
    for doc in rag_docs:
        snippets.append(f"[{doc.title}] {doc.content[:180]}")
        references.append(f"知识库:{doc.title}")
    for article in rag_articles:
        snippets.append(f"[{article.title}] {(article.summary or article.content)[:180]}")
        references.append(f"文章:{article.title}")

    return "\n".join(snippets), references


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_ai(
    message: schemas.ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """与AI助手对话"""
    # 保存用户消息
    user_message = models.ChatMessage(
        user_id=current_user.id,
        message=message.message,
        is_user=True,
        created_at=datetime.utcnow()
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    
    # 生成AI回复（这里使用简单的规则，实际应该集成大模型）
    public_records = _load_public_health_records(db, current_user.id)
    health_context, _ = _build_public_health_context(public_records)
    rag_context, rag_refs = _retrieve_rag_context(db, message.message)
    ai_reply = await generate_ai_response(
        message.message,
        current_user,
        db,
        health_context=health_context,
        rag_context=rag_context,
    )
    
    # 保存AI回复
    ai_message = models.ChatMessage(
        user_id=current_user.id,
        message=ai_reply,
        is_user=False,
        created_at=datetime.utcnow()
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)
    
    return schemas.ChatResponse(
        reply=ai_reply,
        timestamp=ai_message.created_at,
        chat_id=user_message.id,
        references=rag_refs,
        personalization_used=bool(health_context),
    )


@router.get("/chat/history")
async def get_chat_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取对话历史"""
    # 获取用户的所有消息，按时间分组
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == current_user.id
    ).order_by(models.ChatMessage.created_at.desc()).all()
    
    # 简单的对话分组逻辑
    chat_sessions = []
    if messages:
        # 按日期分组对话
        current_date = None
        current_session = None
        
        for msg in messages:
            msg_date = msg.created_at.date()
            
            if current_date != msg_date:
                if current_session:
                    chat_sessions.append(current_session)
                
                current_session = {
                    "id": msg.id,
                    "title": f"对话 {msg_date.strftime('%m-%d')}",
                    "last_message_time": msg.created_at,
                    "message_count": 1
                }
                current_date = msg_date
            else:
                if current_session:
                    current_session["message_count"] += 1
                    current_session["last_message_time"] = msg.created_at
        
        if current_session:
            chat_sessions.append(current_session)
    
    return chat_sessions


@router.get("/chat/{chat_id}/messages")
async def get_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取特定对话的消息"""
    # 获取从该消息ID开始的所有消息
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == current_user.id,
        models.ChatMessage.id >= chat_id
    ).order_by(models.ChatMessage.created_at.asc()).all()
    
    return [
        {
            "id": msg.id,
            "message": msg.message,
            "is_user": msg.is_user,
            "created_at": msg.created_at
        }
        for msg in messages
    ]


@router.delete("/chat/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """删除对话"""
    # 删除从该消息ID开始的所有消息
    deleted_count = db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == current_user.id,
        models.ChatMessage.id >= chat_id
    ).delete()
    
    db.commit()
    return {"message": f"已删除 {deleted_count} 条消息"}


@router.get("/recommendations/{user_id}")
async def get_health_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """获取个性化健康建议"""
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问其他用户的建议")
    
    # 获取用户的健康数据
    health_records = db.query(models.HealthData).filter(
        models.HealthData.user_id == user_id
    ).order_by(models.HealthData.created_at.desc()).limit(10).all()
    
    if not health_records:
        return {"recommendations": ["暂无健康数据，请先记录您的健康信息"]}
    
    # 基于健康数据生成建议
    recommendations = []
    latest_record = health_records[0]
    latest_metrics = _extract_metrics_from_record(latest_record)
    
    # 血压建议
    systolic = latest_metrics.get("blood_pressure_systolic")
    diastolic = latest_metrics.get("blood_pressure_diastolic")
    if systolic and diastolic:
        
        if systolic > 140 or diastolic > 90:
            recommendations.append("您的血压偏高，建议减少盐分摄入，增加有氧运动，必要时咨询医生")
        elif systolic < 90 or diastolic < 60:
            recommendations.append("您的血压偏低，建议适当增加营养摄入，避免长时间站立")
    
    # 心率建议
    heart_rate = latest_metrics.get("heart_rate")
    if heart_rate:
        if heart_rate > 100:
            recommendations.append("您的心率偏快，建议放松心情，减少咖啡因摄入，保证充足睡眠")
        elif heart_rate < 60:
            recommendations.append("您的心率偏慢，如果您不是经常运动的人，建议咨询医生检查")
    
    # 血糖建议
    blood_sugar = latest_metrics.get("blood_sugar")
    if blood_sugar:
        if blood_sugar > 6.1:
            recommendations.append("您的血糖偏高，建议控制碳水化合物摄入，增加运动，定期监测血糖")
        elif blood_sugar < 3.9:
            recommendations.append("您的血糖偏低，建议规律饮食，避免长时间空腹，随身携带零食")
    
    # 生活方式建议
    recommendations.extend([
        "建议每天保持7-8小时的充足睡眠",
        "每周进行至少150分钟的中等强度有氧运动",
        "保持均衡饮食，多吃蔬菜水果，少吃加工食品",
        "定期体检，及时了解自己的健康状况"
    ])
    
    return {"recommendations": recommendations}


@router.get("/home-advice", response_model=schemas.AiHomeAdviceResponse)
async def get_home_health_advice(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    records = _load_public_health_records(db, current_user.id, limit=12)
    if not records:
        return schemas.AiHomeAdviceResponse(
            summary="暂无公开健康数据，记录公开健康数据后可获得个性化建议。",
            recommendations=["先在健康记录中新增至少1条公开记录"],
            insights=[],
            based_on_public_records=0,
        )

    latest_metrics = _extract_metrics_from_record(records[0])
    recommendations: list[str] = []
    insights: list[str] = []

    systolic = latest_metrics.get("blood_pressure_systolic")
    diastolic = latest_metrics.get("blood_pressure_diastolic")
    if systolic and diastolic:
        insights.append(f"最近血压：{systolic}/{diastolic} mmHg")
        if systolic > 140 or diastolic > 90:
            recommendations.append("血压偏高，建议控盐并保持每周有氧运动。")
        elif systolic < 90 or diastolic < 60:
            recommendations.append("血压偏低，建议规律饮食并避免久站。")

    heart_rate = latest_metrics.get("heart_rate")
    if heart_rate:
        insights.append(f"最近心率：{heart_rate} 次/分钟")
        if heart_rate > 100:
            recommendations.append("心率偏快，建议减少咖啡因并保持充足睡眠。")
        elif heart_rate < 60:
            recommendations.append("心率偏慢，若非长期运动人群建议咨询医生。")

    blood_sugar = latest_metrics.get("blood_sugar")
    if blood_sugar:
        insights.append(f"最近血糖：{blood_sugar} mmol/L")
        if blood_sugar > 6.1:
            recommendations.append("血糖偏高，建议减少精制碳水并增加日常步行。")
        elif blood_sugar < 3.9:
            recommendations.append("血糖偏低，建议规律进餐并随身准备补糖食物。")

    if not recommendations:
        recommendations.append("当前指标整体稳定，建议保持规律作息与持续监测。")

    return schemas.AiHomeAdviceResponse(
        summary=f"基于最近{len(records)}条公开健康记录生成建议。",
        recommendations=recommendations,
        insights=insights,
        based_on_public_records=len(records),
    )


@router.post("/analyze")
async def analyze_health_data(
    analysis_data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """分析健康数据"""
    user_id = analysis_data.get("user_id", current_user.id)
    
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权分析其他用户的数据")
    
    # 获取健康数据
    health_records = db.query(models.HealthData).filter(
        models.HealthData.user_id == user_id
    ).order_by(models.HealthData.created_at.desc()).all()
    
    if not health_records:
        return {"analysis": "暂无健康数据可供分析", "insights": []}
    
    insights = []
    
    # 分析趋势
    if len(health_records) >= 2:
        recent = health_records[0]
        previous = health_records[1]
        recent_metrics = _extract_metrics_from_record(recent)
        previous_metrics = _extract_metrics_from_record(previous)
        
        # 体重变化
        recent_weight = recent_metrics.get("weight")
        previous_weight = previous_metrics.get("weight")
        if recent_weight and previous_weight:
            weight_change = recent_weight - previous_weight
            if abs(weight_change) > 0.5:
                insights.append(f"体重变化：{'增加' if weight_change > 0 else '减少'}了{abs(weight_change):.1f}kg")
        
        # 血压变化
        if (
            recent_metrics.get("blood_pressure_systolic")
            and previous_metrics.get("blood_pressure_systolic")
            and recent_metrics.get("blood_pressure_diastolic")
            and previous_metrics.get("blood_pressure_diastolic")
        ):
            sys_change = recent_metrics.get("blood_pressure_systolic") - previous_metrics.get("blood_pressure_systolic")
            dia_change = recent_metrics.get("blood_pressure_diastolic") - previous_metrics.get("blood_pressure_diastolic")
            
            if abs(sys_change) > 5 or abs(dia_change) > 5:
                insights.append(f"血压变化：收缩压{'上升' if sys_change > 0 else '下降'}{abs(sys_change)}mmHg，"
                               f"舒张压{'上升' if dia_change > 0 else '下降'}{abs(dia_change)}mmHg")
    
    # 健康评分
    health_score = calculate_health_score(health_records[0])
    insights.append(f"健康评分：{health_score}/100分")
    
    return {
        "analysis": f"基于您最近的{len(health_records)}条健康数据记录进行分析",
        "insights": insights,
        "health_score": health_score,
        "data_points": len(health_records)
    }


async def generate_ai_response(
    user_message: str,
    current_user: models.User,
    db: Session,
    health_context: str = "",
    rag_context: str = "",
) -> str:
    """生成AI回复（简化版本，实际应该集成大模型）"""
    message_lower = user_message.lower()
    prefix_parts = []
    if health_context:
        prefix_parts.append(f"【用户公开健康数据】{health_context}")
    if rag_context:
        prefix_parts.append(f"【知识库检索摘要】{rag_context}")
    prefix = "\n".join(prefix_parts)
    
    # 健康数据相关
    if "健康数据" in message_lower or "记录" in message_lower:
        return f"{prefix}\n我可以帮您分析健康数据。请持续记录血压、心率、血糖等信息，我会结合您的公开数据给出建议。".strip()
    
    # 血压相关
    elif "血压" in message_lower:
        return (f"{prefix}\n正常血压范围为收缩压90-120mmHg，舒张压60-80mmHg。高血压是指收缩压≥140mmHg或舒张压≥90mmHg。"
                "建议定期监测血压，保持健康饮食，适量运动，控制体重，限制饮酒。").strip()
    
    # 心率相关
    elif "心率" in message_lower:
        return (f"{prefix}\n正常静息心率为60-100次/分钟。运动员心率可能更低。心率过快可能与压力、焦虑、咖啡因等有关；"
                "心率过慢可能是心脏问题的信号。建议定期监测心率，如有异常请咨询医生。").strip()
    
    # 血糖相关
    elif "血糖" in message_lower:
        return (f"{prefix}\n正常空腹血糖为3.9-6.1mmol/L。血糖过高可能是糖尿病，过低可能是低血糖。"
                "建议控制糖分摄入，规律饮食，适量运动，定期监测血糖。").strip()
    
    # 生活方式
    elif "运动" in message_lower or "锻炼" in message_lower:
        return (f"{prefix}\n建议每周进行至少150分钟的中等强度有氧运动，如快走、游泳、骑自行车等。"
                "也可以进行力量训练，每周2-3次。运动有助于控制体重、降低血压、改善血糖。").strip()
    
    elif "饮食" in message_lower or "营养" in message_lower:
        return (f"{prefix}\n建议均衡饮食，多吃蔬菜水果、全谷物、优质蛋白质。减少加工食品、高盐高糖食物。"
                "控制总热量摄入，保持健康体重。每天饮水充足，限制酒精摄入。").strip()
    
    elif "睡眠" in message_lower:
        return (f"{prefix}\n建议成人每天保证7-9小时睡眠。保持规律作息，睡前避免使用电子设备，"
                "创造舒适的睡眠环境。良好的睡眠有助于身体恢复和健康维持。").strip()
    
    # 一般健康建议
    elif "建议" in message_lower or "如何" in message_lower:
        return (f"{prefix}\n保持健康的关键在于：1）均衡饮食和适量运动；2）充足睡眠和压力管理；"
                "3）定期体检和健康监测；4）避免吸烟和过量饮酒；5）保持积极乐观的心态。").strip()
    
    # 默认回复
    else:
        return (f"{prefix}\n我是您的健康助手，可以为您提供健康建议、分析健康数据、回答健康相关问题。"
                "您可以问我关于血压、心率、血糖、运动、饮食等方面的问题。"
                "如需更准确个性化建议，请保持公开健康数据更新并完善知识库。\n"
                "温馨提示：AI建议仅供参考，出现不适请及时就医。").strip()


def calculate_health_score(health_record: models.HealthData) -> int:
    """计算健康评分"""
    score = 100
    metrics = _extract_metrics_from_record(health_record)
    
    # 血压评分
    systolic = metrics.get("blood_pressure_systolic")
    diastolic = metrics.get("blood_pressure_diastolic")
    if systolic and diastolic:
        
        if systolic > 140 or diastolic > 90:
            score -= 20
        elif systolic > 130 or diastolic > 85:
            score -= 10
        elif systolic < 90 or diastolic < 60:
            score -= 15
    
    # 心率评分
    heart_rate = metrics.get("heart_rate")
    if heart_rate:
        if heart_rate > 100:
            score -= 15
        elif heart_rate < 60:
            score -= 10
    
    # 血糖评分
    blood_sugar = metrics.get("blood_sugar")
    if blood_sugar:
        if blood_sugar > 6.1:
            score -= 20
        elif blood_sugar < 3.9:
            score -= 15
    
    # BMI评分（如果有身高体重数据）
    height = metrics.get("height")
    weight = metrics.get("weight")
    if height and weight:
        bmi = weight / ((height / 100) ** 2)
        if bmi > 30:
            score -= 20
        elif bmi > 25:
            score -= 10
        elif bmi < 18.5:
            score -= 10
    
    return max(0, score)
