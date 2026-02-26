from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app import models, schemas
from app.routers.auth import get_current_user


router = APIRouter()


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
    ai_reply = await generate_ai_response(message.message, current_user, db)
    
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
        chat_id=user_message.id
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
    ).order_by(models.HealthData.recorded_at.desc()).limit(10).all()
    
    if not health_records:
        return {"recommendations": ["暂无健康数据，请先记录您的健康信息"]}
    
    # 基于健康数据生成建议
    recommendations = []
    latest_record = health_records[0]
    
    # 血压建议
    if latest_record.blood_pressure_systolic and latest_record.blood_pressure_diastolic:
        systolic = latest_record.blood_pressure_systolic
        diastolic = latest_record.blood_pressure_diastolic
        
        if systolic > 140 or diastolic > 90:
            recommendations.append("您的血压偏高，建议减少盐分摄入，增加有氧运动，必要时咨询医生")
        elif systolic < 90 or diastolic < 60:
            recommendations.append("您的血压偏低，建议适当增加营养摄入，避免长时间站立")
    
    # 心率建议
    if latest_record.heart_rate:
        if latest_record.heart_rate > 100:
            recommendations.append("您的心率偏快，建议放松心情，减少咖啡因摄入，保证充足睡眠")
        elif latest_record.heart_rate < 60:
            recommendations.append("您的心率偏慢，如果您不是经常运动的人，建议咨询医生检查")
    
    # 血糖建议
    if latest_record.blood_sugar:
        if latest_record.blood_sugar > 6.1:
            recommendations.append("您的血糖偏高，建议控制碳水化合物摄入，增加运动，定期监测血糖")
        elif latest_record.blood_sugar < 3.9:
            recommendations.append("您的血糖偏低，建议规律饮食，避免长时间空腹，随身携带零食")
    
    # 生活方式建议
    recommendations.extend([
        "建议每天保持7-8小时的充足睡眠",
        "每周进行至少150分钟的中等强度有氧运动",
        "保持均衡饮食，多吃蔬菜水果，少吃加工食品",
        "定期体检，及时了解自己的健康状况"
    ])
    
    return {"recommendations": recommendations}


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
    ).order_by(models.HealthData.recorded_at.desc()).all()
    
    if not health_records:
        return {"analysis": "暂无健康数据可供分析", "insights": []}
    
    insights = []
    
    # 分析趋势
    if len(health_records) >= 2:
        recent = health_records[0]
        previous = health_records[1]
        
        # 体重变化
        if recent.weight and previous.weight:
            weight_change = recent.weight - previous.weight
            if abs(weight_change) > 0.5:
                insights.append(f"体重变化：{'增加' if weight_change > 0 else '减少'}了{abs(weight_change):.1f}kg")
        
        # 血压变化
        if (recent.blood_pressure_systolic and previous.blood_pressure_systolic and
            recent.blood_pressure_diastolic and previous.blood_pressure_diastolic):
            sys_change = recent.blood_pressure_systolic - previous.blood_pressure_systolic
            dia_change = recent.blood_pressure_diastolic - previous.blood_pressure_diastolic
            
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


async def generate_ai_response(user_message: str, current_user: models.User, db: Session) -> str:
    """生成AI回复（简化版本，实际应该集成大模型）"""
    message_lower = user_message.lower()
    
    # 健康数据相关
    if "健康数据" in message_lower or "记录" in message_lower:
        return "我可以帮您分析健康数据。请在健康数据页面记录您的血压、心率、血糖等信息，我会为您提供专业的健康建议。"
    
    # 血压相关
    elif "血压" in message_lower:
        return ("正常血压范围为收缩压90-120mmHg，舒张压60-80mmHg。高血压是指收缩压≥140mmHg或舒张压≥90mmHg。"
                "建议定期监测血压，保持健康饮食，适量运动，控制体重，限制饮酒。")
    
    # 心率相关
    elif "心率" in message_lower:
        return ("正常静息心率为60-100次/分钟。运动员心率可能更低。心率过快可能与压力、焦虑、咖啡因等有关；"
                "心率过慢可能是心脏问题的信号。建议定期监测心率，如有异常请咨询医生。")
    
    # 血糖相关
    elif "血糖" in message_lower:
        return ("正常空腹血糖为3.9-6.1mmol/L。血糖过高可能是糖尿病，过低可能是低血糖。"
                "建议控制糖分摄入，规律饮食，适量运动，定期监测血糖。")
    
    # 生活方式
    elif "运动" in message_lower or "锻炼" in message_lower:
        return ("建议每周进行至少150分钟的中等强度有氧运动，如快走、游泳、骑自行车等。"
                "也可以进行力量训练，每周2-3次。运动有助于控制体重、降低血压、改善血糖。")
    
    elif "饮食" in message_lower or "营养" in message_lower:
        return ("建议均衡饮食，多吃蔬菜水果、全谷物、优质蛋白质。减少加工食品、高盐高糖食物。"
                "控制总热量摄入，保持健康体重。每天饮水充足，限制酒精摄入。")
    
    elif "睡眠" in message_lower:
        return ("建议成人每天保证7-9小时睡眠。保持规律作息，睡前避免使用电子设备，"
                "创造舒适的睡眠环境。良好的睡眠有助于身体恢复和健康维持。")
    
    # 一般健康建议
    elif "建议" in message_lower or "如何" in message_lower:
        return ("保持健康的关键在于：1）均衡饮食和适量运动；2）充足睡眠和压力管理；"
                "3）定期体检和健康监测；4）避免吸烟和过量饮酒；5）保持积极乐观的心态。")
    
    # 默认回复
    else:
        return ("我是您的健康助手，可以为您提供健康建议、分析健康数据、回答健康相关问题。"
                "您可以问我关于血压、心率、血糖、运动、饮食等方面的问题。"
                "如需个性化建议，请先在健康数据页面记录您的健康信息。")


def calculate_health_score(health_record: models.HealthData) -> int:
    """计算健康评分"""
    score = 100
    
    # 血压评分
    if health_record.blood_pressure_systolic and health_record.blood_pressure_diastolic:
        systolic = health_record.blood_pressure_systolic
        diastolic = health_record.blood_pressure_diastolic
        
        if systolic > 140 or diastolic > 90:
            score -= 20
        elif systolic > 130 or diastolic > 85:
            score -= 10
        elif systolic < 90 or diastolic < 60:
            score -= 15
    
    # 心率评分
    if health_record.heart_rate:
        heart_rate = health_record.heart_rate
        if heart_rate > 100:
            score -= 15
        elif heart_rate < 60:
            score -= 10
    
    # 血糖评分
    if health_record.blood_sugar:
        blood_sugar = health_record.blood_sugar
        if blood_sugar > 6.1:
            score -= 20
        elif blood_sugar < 3.9:
            score -= 15
    
    # BMI评分（如果有身高体重数据）
    if health_record.height and health_record.weight:
        bmi = health_record.weight / ((health_record.height / 100) ** 2)
        if bmi > 30:
            score -= 20
        elif bmi > 25:
            score -= 10
        elif bmi < 18.5:
            score -= 10
    
    return max(0, score)
