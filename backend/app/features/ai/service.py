from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from typing import Optional

from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.features.auth.service import AuthService
from app.features.blockchain.encryption import decrypt_binary, decrypt_text, normalize_private_key

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


MAX_CONTEXT_RECORDS = 6
MAX_HOME_ADVICE_RECORDS = 12
MAX_PDF_SNIPPET_LENGTH = 360
MAX_TEXT_SNIPPET_LENGTH = 220


@dataclass
class RecordContext:
    record_id: int
    title: str
    file_type: str
    created_at: datetime
    metrics: dict
    summary: str


def public_storage_key() -> str:
    return f"health-data-public::{settings.SECRET_KEY or 'health-data-default'}"


def json_loads_object(text: Optional[str]) -> dict:
    if not text:
        return {}
    try:
        value = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def normalize_multiline_text(text: Optional[str]) -> str:
    if not text:
        return ""
    lines = [line.strip() for line in str(text).replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line).strip()


def compact_text(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", normalize_multiline_text(text)).strip()


def truncate_text(text: Optional[str], limit: int) -> str:
    compact = compact_text(text)
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def extract_pdf_text(file_bytes: Optional[bytes]) -> str:
    if not file_bytes or PdfReader is None:
        return ""
    try:
        reader = PdfReader(BytesIO(file_bytes))
        parts: list[str] = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return normalize_multiline_text("\n".join(parts))
    except Exception:  # noqa: BLE001
        return ""


def record_title(record: models.HealthData) -> str:
    if record.data_title and record.data_title.strip():
        return record.data_title.strip()
    return f"PDF记录 #{record.id}" if record.file_type == "pdf" else f"健康记录 #{record.id}"


def metric_lines(metrics: Optional[dict]) -> list[str]:
    if not isinstance(metrics, dict):
        return []
    items: list[str] = []
    systolic = metrics.get("blood_pressure_systolic")
    diastolic = metrics.get("blood_pressure_diastolic")
    if systolic is not None and diastolic is not None:
        items.append(f"血压 {systolic}/{diastolic} mmHg")
    if metrics.get("heart_rate") is not None:
        items.append(f"心率 {metrics['heart_rate']} 次/分")
    if metrics.get("blood_sugar") is not None:
        items.append(f"血糖 {metrics['blood_sugar']} mmol/L")
    if metrics.get("weight") is not None:
        items.append(f"体重 {metrics['weight']} kg")
    if metrics.get("height") is not None:
        items.append(f"身高 {metrics['height']} cm")
    if metrics.get("blood_lipid") not in (None, ""):
        items.append(f"血脂 {metrics['blood_lipid']}")
    return items


def summarize_profile_payload(profile_text: Optional[str]) -> str:
    payload = json_loads_object(profile_text)
    if not payload:
        return truncate_text(profile_text, 240)
    pairs: list[str] = []
    field_labels = [
        ("gender", "性别"),
        ("age", "年龄"),
        ("height", "身高"),
        ("weight", "体重"),
        ("medical_history", "病史"),
        ("allergies", "过敏史"),
        ("medications", "长期用药"),
        ("sleep", "睡眠"),
        ("exercise", "运动"),
    ]
    for key, label in field_labels:
        value = payload.get(key)
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            value = "、".join(str(item) for item in value if str(item).strip())
        pairs.append(f"{label}：{value}")
    return "；".join(pairs[:6])


def public_profile_summary(user: models.User) -> str:
    if not user.profile_is_public or not user.public_profile_data:
        return ""
    return summarize_profile_payload(user.public_profile_data)


def user_private_keys(user: models.User) -> list[str]:
    keys: list[str] = []
    if user.encrypted_private_key:
        try:
            keys.append(normalize_private_key(AuthService.decrypt_private_key_from_storage(user.encrypted_private_key)))
        except ValueError:
            pass
    if user.private_key_hash:
        try:
            keys.append(normalize_private_key(user.private_key_hash))
        except ValueError:
            pass
    unique: list[str] = []
    for key in keys:
        if key not in unique:
            unique.append(key)
    return unique


def decrypt_with_keys(cipher_text: str, keys: list[str]) -> str:
    for key in keys:
        try:
            return decrypt_text(cipher_text, key)
        except ValueError:
            continue
    raise ValueError("unable to decrypt")


def _resolve_record_text_payload(record: models.HealthData, private_key: Optional[str] = None) -> str:
    if record.data_content:
        return record.data_content
    storage_key = public_storage_key() if record.is_public else private_key
    if record.encrypted_data_content and storage_key:
        try:
            return decrypt_text(record.encrypted_data_content, storage_key)
        except ValueError:
            return ""
    return ""


def _resolve_record_pdf_bytes(record: models.HealthData, private_key: Optional[str] = None) -> bytes:
    if record.pdf_data:
        return record.pdf_data
    storage_key = public_storage_key() if record.is_public else private_key
    if record.encrypted_pdf_data and storage_key:
        try:
            return decrypt_binary(record.encrypted_pdf_data, storage_key)
        except ValueError:
            return b""
    return b""


def _build_text_record_context(record: models.HealthData, payload_text: str) -> RecordContext:
    payload = json_loads_object(payload_text)
    metrics = payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}
    free_text = payload.get("other_text")
    if not free_text and not metrics:
        free_text = payload_text
    parts = metric_lines(metrics)
    if free_text:
        parts.append(truncate_text(free_text, MAX_TEXT_SNIPPET_LENGTH))
    summary = "；".join(part for part in parts if part).strip("；")
    return RecordContext(
        record_id=record.id,
        title=record_title(record),
        file_type="text",
        created_at=record.created_at,
        metrics=metrics,
        summary=summary or "无可解析文本",
    )


def _build_pdf_record_context(record: models.HealthData, pdf_bytes: bytes) -> RecordContext:
    pdf_text = extract_pdf_text(pdf_bytes)
    return RecordContext(
        record_id=record.id,
        title=record_title(record),
        file_type="pdf",
        created_at=record.created_at,
        metrics={},
        summary=truncate_text(pdf_text, MAX_PDF_SNIPPET_LENGTH) or "PDF 内容暂未提取到文本",
    )


def build_record_context(record: models.HealthData, private_key: Optional[str] = None) -> Optional[RecordContext]:
    if record.file_type == "pdf":
        pdf_bytes = _resolve_record_pdf_bytes(record, private_key)
        if not pdf_bytes:
            return None
        return _build_pdf_record_context(record, pdf_bytes)

    payload_text = _resolve_record_text_payload(record, private_key)
    if not payload_text:
        return None
    return _build_text_record_context(record, payload_text)


def build_private_record_context(record: models.HealthData, keys: list[str]) -> Optional[RecordContext]:
    if record.file_type == "pdf":
        pdf_bytes = record.pdf_data
        if not pdf_bytes and record.encrypted_pdf_data:
            for key in keys:
                try:
                    pdf_bytes = decrypt_binary(record.encrypted_pdf_data, key)
                    break
                except ValueError:
                    continue
        if not pdf_bytes:
            return None
        return _build_pdf_record_context(record, pdf_bytes)

    payload_text = record.data_content
    if not payload_text and record.encrypted_data_content:
        try:
            payload_text = decrypt_with_keys(record.encrypted_data_content, keys)
        except ValueError:
            return None
    if not payload_text:
        return None
    return _build_text_record_context(record, payload_text)


def get_public_records(db: Session, user_id: int, limit: Optional[int] = MAX_HOME_ADVICE_RECORDS) -> list[models.HealthData]:
    query = (
        db.query(models.HealthData)
        .filter(models.HealthData.user_id == user_id, models.HealthData.is_public.is_(True))
        .order_by(models.HealthData.created_at.desc())
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def build_public_health_context(db: Session, user: models.User, limit: int = MAX_CONTEXT_RECORDS) -> tuple[str, int]:
    contexts: list[str] = []
    public_records = get_public_records(db, user.id, limit)
    used = 0
    for record in public_records:
        context = build_record_context(record)
        if not context:
            continue
        created_at = context.created_at.strftime("%Y-%m-%d %H:%M")
        prefix = f"{created_at}｜{context.title}"
        if context.file_type == "pdf":
            contexts.append(f"{prefix}（公开 PDF）：{context.summary}")
        else:
            contexts.append(f"{prefix}：{context.summary}")
        used += 1
    return "\n".join(contexts), used


def build_private_context_options(db: Session, user: models.User) -> list[schemas.AiPrivateContextOption]:
    can_use = bool(user_private_keys(user))
    items: list[schemas.AiPrivateContextOption] = []
    if user.encrypted_profile_data and not user.profile_is_public:
        items.append(
            schemas.AiPrivateContextOption(
                id="profile:self",
                type="profile",
                label="私密个人档案",
                description="病史、过敏史、长期用药等非公开档案",
                available=can_use,
            )
        )

    records = (
        db.query(models.HealthData)
        .filter(models.HealthData.user_id == user.id, models.HealthData.is_public.is_(False))
        .order_by(models.HealthData.created_at.desc())
        .all()
    )
    for record in records:
        is_pdf = record.file_type == "pdf"
        items.append(
            schemas.AiPrivateContextOption(
                id=f"record:{record.id}",
                type="record_pdf" if is_pdf else "record_text",
                label=record_title(record),
                description=(
                    f"{record.created_at.strftime('%Y-%m-%d %H:%M')}｜将自动解密并读取 PDF 内容"
                    if is_pdf
                    else f"{record.created_at.strftime('%Y-%m-%d %H:%M')}｜将自动解密并读取记录内容"
                ),
                available=can_use,
                created_at=record.created_at,
            )
        )
    return items


def build_private_context(db: Session, user: models.User, selected_ids: list[str]) -> tuple[str, int]:
    selected = [str(item).strip() for item in (selected_ids or []) if str(item).strip()]
    if not selected:
        return "", 0

    keys = user_private_keys(user)
    if not keys:
        return "", 0

    blocks: list[str] = []
    used = 0

    if "profile:self" in selected and user.encrypted_profile_data and not user.profile_is_public:
        try:
            profile_text = decrypt_with_keys(user.encrypted_profile_data, keys)
            profile_summary = summarize_profile_payload(profile_text) or truncate_text(profile_text, 240)
            if profile_summary:
                blocks.append(f"【用户授权的私密档案】\n{profile_summary}")
                used += 1
        except ValueError:
            pass

    record_ids: list[int] = []
    for item in selected:
        if item.startswith("record:"):
            try:
                record_ids.append(int(item.split(":", 1)[1]))
            except ValueError:
                continue

    if record_ids:
        records = (
            db.query(models.HealthData)
            .filter(models.HealthData.user_id == user.id, models.HealthData.is_public.is_(False), models.HealthData.id.in_(record_ids))
            .order_by(models.HealthData.created_at.desc())
            .all()
        )
        lines: list[str] = []
        for record in records:
            context = build_private_record_context(record, keys)
            if not context:
                continue
            created_at = context.created_at.strftime("%Y-%m-%d %H:%M")
            type_label = "私密 PDF" if context.file_type == "pdf" else "私密记录"
            lines.append(f"- {context.title}（{type_label}，{created_at}）：{context.summary}")
            used += 1
        if lines:
            blocks.append("【用户授权的私密健康数据】\n" + "\n".join(lines))

    return "\n\n".join(blocks), used


def _recent_numeric_values(metrics_samples: list[dict], key: str, limit: int = 3) -> list[float]:
    values: list[float] = []
    for sample in metrics_samples[:limit]:
        value = sample.get(key) if isinstance(sample, dict) else None
        if value in (None, ""):
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def _append_recent_trend_recommendations(recommendations: list[str], metrics_samples: list[dict]) -> None:
    recent_weights = _recent_numeric_values(metrics_samples, "weight", limit=3)
    if len(recent_weights) >= 2:
        delta = recent_weights[0] - recent_weights[-1]
        if abs(delta) >= 1.5:
            trend = "上升" if delta > 0 else "下降"
            recommendations.append(f"最近几次公开记录里体重呈{trend}趋势，建议优先关注近一周饮食和运动变化。")

    recent_heart_rates = _recent_numeric_values(metrics_samples, "heart_rate", limit=3)
    if len(recent_heart_rates) >= 2 and recent_heart_rates[0] - recent_heart_rates[-1] >= 8:
        recommendations.append("最新心率相比更早记录偏高，建议近期减少熬夜并留意压力和运动恢复情况。")

    recent_sugars = _recent_numeric_values(metrics_samples, "blood_sugar", limit=3)
    if len(recent_sugars) >= 2 and recent_sugars[0] - recent_sugars[-1] >= 0.5:
        recommendations.append("最新血糖较前几次记录有上升，建议优先回看最近饮食和作息变化。")


def _collect_home_advice_recommendations(metrics_samples: list[dict], knowledge_text: str, profile_text: str) -> list[str]:
    recommendations: list[str] = []
    latest = metrics_samples[0] if metrics_samples else {}

    systolic = latest.get("blood_pressure_systolic")
    diastolic = latest.get("blood_pressure_diastolic")
    if systolic is not None and diastolic is not None:
        if systolic >= 140 or diastolic >= 90:
            recommendations.append("近期公开记录提示血压偏高，建议继续监测血压并控制盐分摄入。")
        elif systolic < 90 or diastolic < 60:
            recommendations.append("近期公开记录提示血压偏低，建议规律作息、补充水分，如伴头晕请及时就医。")

    heart_rate = latest.get("heart_rate")
    if heart_rate is not None and heart_rate > 100:
        recommendations.append("近期心率偏快，建议先减少熬夜、咖啡因和高强度连续负荷。")

    blood_sugar = latest.get("blood_sugar")
    if blood_sugar is not None and blood_sugar > 6.1:
        recommendations.append("血糖指标偏高，建议控制精制糖摄入并增加规律步行或有氧运动。")

    if latest.get("height") not in (None, 0) and latest.get("weight") not in (None, 0):
        try:
            bmi = float(latest["weight"]) / ((float(latest["height"]) / 100) ** 2)
            if bmi >= 28:
                recommendations.append("BMI 偏高，建议优先保持稳定热量缺口和每周规律运动。")
            elif bmi < 18.5:
                recommendations.append("BMI 偏低，建议关注优质蛋白与规律进食。")
        except Exception:  # noqa: BLE001
            pass

    _append_recent_trend_recommendations(recommendations, metrics_samples)

    merged_text = f"{profile_text}\n{knowledge_text}".lower()
    keyword_rules = [
        ("睡眠", "公开资料提到睡眠问题，建议固定入睡时间并减少夜间电子屏幕暴露。"),
        ("焦虑", "如果近期有焦虑或压力线索，建议加入放松训练并尽量保证连续睡眠。"),
        ("过敏", "公开资料包含过敏信息时，建议整理过敏原和既往反应，便于后续问答更精准。"),
        ("高血压", "若公开资料涉及高血压，请继续关注晨起与晚间血压变化。"),
        ("糖尿病", "若公开资料涉及糖代谢问题，建议记录餐后血糖或饮食波动。"),
        ("体检", "上传的公开体检/检查 PDF 已纳入建议，建议结合异常项做复查计划。"),
    ]
    for keyword, message in keyword_rules:
        if keyword.lower() in merged_text and message not in recommendations:
            recommendations.append(message)

    defaults = [
        "建议继续补充公开健康数据，这样首页建议与 AI 问答会更贴近你的实际情况。",
        "建议把长期趋势数据按周维护，例如血压、体重、睡眠和运动时长。",
        "如出现持续异常指标或明显不适，请优先线下就医。"
    ]
    for message in defaults:
        if len(recommendations) >= 4:
            break
        if message not in recommendations:
            recommendations.append(message)
    return recommendations[:4]


def build_home_advice_payload(db: Session, user: models.User) -> dict:
    public_records = get_public_records(db, user.id, MAX_HOME_ADVICE_RECORDS)
    profile_summary = public_profile_summary(user)

    record_contexts: list[RecordContext] = []
    metrics_samples: list[dict] = []
    pdf_count = 0
    for record in public_records:
        context = build_record_context(record)
        if not context:
            continue
        record_contexts.append(context)
        if context.metrics:
            metrics_samples.append(context.metrics)
        if context.file_type == "pdf":
            pdf_count += 1

    if not record_contexts and not profile_summary:
        return {
            "summary": "暂无公开健康数据，录入公开文本或 PDF 后将自动生成并保存首页个性化建议。",
            "recommendations": ["先新增至少 1 条公开健康记录，或将公开档案补充完整。"],
            "insights": [],
            "based_on_public_records": 0,
            "updated_at": datetime.utcnow().isoformat(),
        }

    insights: list[str] = []
    if profile_summary:
        insights.append("已结合公开个人档案")
    latest_context = record_contexts[0] if record_contexts else None
    if latest_context and latest_context.metrics:
        insights.extend(metric_lines(latest_context.metrics))
    if pdf_count:
        insights.append(f"已读取 {pdf_count} 份公开 PDF")

    knowledge_text = "\n".join(context.summary for context in record_contexts)
    recommendations = _collect_home_advice_recommendations(metrics_samples, knowledge_text, profile_summary)

    source_count = len(record_contexts)
    recent_focus_count = min(3, source_count)
    summary_parts: list[str] = []
    if source_count:
        summary_parts.append(f"已基于 {source_count} 条公开健康记录生成并保存建议")
        if recent_focus_count:
            summary_parts.append(f"并优先参考最近 {recent_focus_count} 条更新数据")
    if pdf_count:
        summary_parts.append(f"其中包含 {pdf_count} 份 PDF")
    if profile_summary:
        summary_parts.append("并结合了公开个人档案")
    if latest_context and latest_context.summary:
        summary_parts.append(f"最近一次记录重点：{truncate_text(latest_context.summary, 80)}")

    return {
        "summary": "，".join(summary_parts) + "。",
        "recommendations": recommendations,
        "insights": insights[:6],
        "based_on_public_records": source_count,
        "updated_at": datetime.utcnow().isoformat(),
    }


def refresh_user_home_advice(db: Session, user: models.User, *, commit: bool = True) -> dict:
    payload = build_home_advice_payload(db, user)
    user.home_ai_advice_cache = json.dumps(payload, ensure_ascii=False)
    if commit:
        db.commit()
        db.refresh(user)
    return payload


def invalidate_user_home_advice(db: Session, user: models.User, *, commit: bool = True) -> None:
    user.home_ai_advice_cache = None
    if commit:
        db.commit()
        db.refresh(user)


def save_user_home_advice_payload(db: Session, user: models.User, payload: dict, *, commit: bool = True) -> dict:
    user.home_ai_advice_cache = json.dumps(payload, ensure_ascii=False)
    if commit:
        db.commit()
        db.refresh(user)
    return payload


def load_cached_home_advice(user: models.User) -> Optional[dict]:
    if not user.home_ai_advice_cache:
        return None
    try:
        payload = json.loads(user.home_ai_advice_cache)
    except (TypeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def get_or_refresh_user_home_advice(db: Session, user: models.User) -> dict:
    cached = load_cached_home_advice(user)
    if cached and isinstance(cached.get("recommendations", []), list):
        cached.setdefault("summary", "暂无建议")
        cached.setdefault("recommendations", [])
        cached.setdefault("insights", [])
        cached.setdefault("based_on_public_records", 0)
        return cached
    return refresh_user_home_advice(db, user)
