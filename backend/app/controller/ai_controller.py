from __future__ import annotations

import asyncio
import json
import logging
import re
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.database import SessionLocal, get_db
from app.service.ai_service import (
    build_private_context,
    build_private_context_options,
    build_public_health_context,
    build_record_context,
    get_public_records,
    json_loads_object,
    load_cached_home_advice,
    metric_lines,
    public_profile_summary,
    save_user_home_advice_payload,
    truncate_text,
)
from app.features.auth.dependencies import get_current_user
from app.service.rag_index_service import RagIndexError, search_rag_knowledge


router = APIRouter()
logger = logging.getLogger(__name__)


def _get_bool_system_setting(db: Session, key: str, default_value: bool) -> bool:
    row = db.query(models.SystemSetting).filter(models.SystemSetting.setting_key == key).first()
    if not row:
        return default_value
    try:
        value = json.loads(row.setting_value)
    except Exception:  # noqa: BLE001
        return default_value
    return bool(value)


def _ensure_ai_service_enabled(db: Session) -> None:
    if _get_bool_system_setting(db, "maintenance_mode", False):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="System is under maintenance")
    if not _get_bool_system_setting(db, "ai_enabled", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="AI service is disabled")

HEALTH_TERMS = ["健康", "血压", "血糖", "心率", "睡眠", "体重", "饮食", "运动", "慢病", "过敏", "体检"]


def _query_terms(question: str) -> list[str]:
    question = (question or "").strip()
    if not question:
        return []
    terms = [seg for seg in re.findall(r"[A-Za-z0-9_+-]+|[\u4e00-\u9fff]{2,}", question) if seg.strip()]
    for term in HEALTH_TERMS:
        if term in question and term not in terms:
            terms.append(term)
    terms.append(question)
    return terms[:12]


def _snippet(content: str, terms: list[str], max_length: int = 140) -> str:
    compact = re.sub(r"\s+", " ", content or "").strip()
    if len(compact) <= max_length:
        return compact
    lower = compact.lower()
    for term in terms:
        idx = lower.find(term.lower())
        if idx >= 0:
            start = max(0, idx - max_length // 3)
            end = min(len(compact), start + max_length)
            return ("..." if start > 0 else "") + compact[start:end] + ("..." if end < len(compact) else "")
    return compact[:max_length] + "..."


def _score(texts: list[str], question: str, terms: list[str]) -> int:
    score = 0
    question_lower = question.lower()
    for text in texts:
        lower = (text or "").lower()
        if question_lower and question_lower in lower:
            score += 8
        for term in terms:
            if term.lower() in lower:
                score += 2
    return score


def _keyword_rag_context(db: Session, question: str, terms: list[str]) -> tuple[str, list[str]]:
    candidates: list[tuple[int, datetime, str, str]] = []
    docs = db.query(models.RagKnowledgeDocument).filter(models.RagKnowledgeDocument.is_active.is_(True)).all()
    for doc in docs:
        score = _score([doc.title, doc.category, doc.content, doc.tags or "", doc.source or ""], question, terms)
        if score > 0:
            candidates.append(
                (
                    score,
                    doc.updated_at,
                    f"Knowledge: {doc.title}",
                    f"[Knowledge] {doc.title}\n{_snippet(doc.content, terms)}",
                )
            )

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    chosen = candidates[: settings.AI_RAG_LIMIT]
    return "\n\n".join(item[3] for item in chosen), [item[2] for item in chosen]


def _rag_context(db: Session, question: str) -> tuple[str, list[str]]:
    terms = _query_terms(question)
    if not terms:
        return "", []

    try:
        raw_hits = search_rag_knowledge(question, max(settings.RAG_VECTOR_TOP_K, settings.AI_RAG_LIMIT * 3))
    except RagIndexError as exc:
        logger.warning("RAG vector retrieval failed, fallback to keyword retrieval: %s", exc)
        return _keyword_rag_context(db, question, terms)

    if not raw_hits:
        return _keyword_rag_context(db, question, terms)

    deduped_hits: dict[int, tuple[float, datetime, str, str]] = {}
    for hit in raw_hits:
        lexical_bonus = _score(
            [hit.title, hit.category, hit.content, ",".join(hit.tags), hit.source or ""],
            question,
            terms,
        )
        candidate = (
            hit.score * 100 + lexical_bonus,
            hit.updated_at,
            f"Knowledge: {hit.title}",
            f"[Knowledge] {hit.title}\n{_snippet(hit.content, terms)}",
        )
        existing = deduped_hits.get(hit.document_id)
        if existing is None or candidate[0] > existing[0]:
            deduped_hits[hit.document_id] = candidate

    ranked_hits = sorted(deduped_hits.values(), key=lambda item: (item[0], item[1]), reverse=True)
    chosen = ranked_hits[: settings.AI_RAG_LIMIT]
    if not chosen:
        return _keyword_rag_context(db, question, terms)
    return "\n\n".join(item[3] for item in chosen), [item[2] for item in chosen]


def _chat_history(db: Session, user_id: int, chat_id: Optional[int]) -> str:
    if not chat_id:
        return ""
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == user_id, models.ChatMessage.session_id == chat_id)
        .order_by(models.ChatMessage.created_at.asc())
        .limit(settings.AI_CHAT_HISTORY_LIMIT)
        .all()
    )
    return "\n".join(f"{'用户' if message.is_user else '助手'}：{message.message}" for message in messages)


def _history_session_title(message: models.ChatMessage) -> str:
    raw = (message.message or "").strip()
    if not raw:
        return f"对话 {message.created_at.strftime('%m-%d')}"
    compact = re.sub(r"\s+", " ", raw)
    return compact[:18] + ("..." if len(compact) > 18 else "")


def _prompt(
    *,
    user_message: str,
    profile_context: str,
    health_context: str,
    private_context: str,
    rag_context: str,
    history_context: str,
) -> str:
    sections = ["请结合上下文直接回答用户问题。"]
    if profile_context:
        sections.append(f"【用户公开档案】\n{profile_context}")
    if health_context:
        sections.append(f"【用户公开健康数据】\n{health_context}")
    if private_context:
        sections.append(f"【用户授权的私密数据】\n{private_context}")
    if rag_context:
        sections.append(f"【知识库 / RAG 检索结果】\n{rag_context}")
    if history_context:
        sections.append(f"【本轮对话上下文】\n{history_context}")
    sections.append(
        "【要求】\n"
        "1. 先直接回答问题。\n"
        "2. 如使用了用户公开数据或用户授权私密数据，请明确说明依据。\n"
        "3. 没有数据支撑时不要编造。\n"
        "4. 尽量简洁，给出 2-3 条可执行建议。\n"
        "5. 使用中文，不输出思维过程。"
    )
    sections.append(f"【用户当前问题】\n{user_message}")
    return "\n\n".join(section for section in sections if section.strip())


def _system_prompt() -> str:
    return (
        "你是本地健康管理助手。\n"
        "优先基于用户公开健康数据、用户明确授权的私密数据和知识库检索结果回答。\n"
        "私密数据只用于当前这一次回答。\n"
        "不要编造，不要输出思维过程。\n"
        "避免直接诊断；如出现高风险症状，提醒及时线下就医。"
    )


def _clean_response(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.I | re.S).strip()


def _extract_json_block(text: str) -> dict | None:
    cleaned = (text or "").strip()
    if not cleaned:
        return None
    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, flags=re.S | re.I)
    if fenced_match:
        cleaned = fenced_match.group(1).strip()
    else:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start : end + 1]
    try:
        payload = json.loads(cleaned)
    except (TypeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _home_advice_rag_query(profile_context: str, record_summaries: list[str]) -> str:
    latest_focus = " ".join(record_summaries[:3])
    return "\n".join(part for part in [profile_context, latest_focus] if part).strip()


def _home_advice_prompt(
    *,
    profile_context: str,
    recent_records_text: str,
    trend_records_text: str,
    rag_context: str,
) -> str:
    sections = [
        "Generate personalized homepage health advice for this user.",
        "Use the most recent public records as the highest-priority evidence, then use older records for trend reference.",
        "Also use the RAG knowledge as supporting context.",
        'Output JSON only: {"summary":"", "recommendations":["", ""], "insights":["", ""], "based_on_public_records":0}',
        "Respond in Chinese. Do not output markdown. Do not output any text outside the JSON object.",
        "recommendations max 3 items; insights max 4 items.",
    ]
    if profile_context:
        sections.append(f"[Public Profile]\n{profile_context}")
    if recent_records_text:
        sections.append(f"[Recent Public Health Records - Highest Weight]\n{recent_records_text}")
    if trend_records_text:
        sections.append(f"[Older Public Health Records - Trend Reference]\n{trend_records_text}")
    if rag_context:
        sections.append(f"[RAG Knowledge]\n{rag_context}")
    sections.append(
        "[Output Requirements]\n"
        "1. summary should be 1-2 short Chinese sentences.\n"
        "2. recommendations should be generated directly by the LLM based on the user's data and RAG knowledge.\n"
        "3. Each recommendation must be specific and actionable, preferably with frequency, amount, duration, or clear steps.\n"
        "4. Avoid vague wording like '多关注/注意/保持/留意'; instead say exactly what the user should do.\n"
        "5. Example of good recommendation: '未来 7 天把晚睡控制在 23:30 前，每天晚饭后快走 20-30 分钟，并连续记录晨起血压。'\n"
        "6. If new data conflicts with old data, prioritize the new data.\n"
        "7. If evidence is limited, say so briefly."
    )
    return "\n\n".join(section for section in sections if section.strip())


def _normalize_home_advice_payload(payload: dict | None, based_on_public_records: int) -> dict:
    source = payload if isinstance(payload, dict) else {}
    summary = str(source.get("summary") or "暂无建议").strip()
    recommendations_raw = source.get("recommendations")
    insights_raw = source.get("insights")
    recommendations = [str(item).strip() for item in (recommendations_raw or []) if str(item).strip()][:3]
    insights = [str(item).strip() for item in (insights_raw or []) if str(item).strip()][:4]
    return {
        "summary": summary,
        "recommendations": recommendations,
        "insights": insights,
        "based_on_public_records": based_on_public_records,
        "updated_at": datetime.utcnow().isoformat(),
        "generator": "ollama_rag_v2",
    }


async def _generate_home_advice_payload(db: Session, current_user: models.User) -> dict:
    public_records = get_public_records(db, current_user.id)
    record_contexts = [context for record in public_records if (context := build_record_context(record))]
    profile_context = public_profile_summary(current_user)
    based_on_public_records = len(record_contexts)

    if not record_contexts and not profile_context:
        payload = {
            "summary": "暂无公开健康数据，录入公开文本、PDF 或公开档案后，AI 会为你生成更具体的个性化建议。",
            "recommendations": ["先新增至少 1 条公开健康数据，首页 AI 建议才会更贴近你的真实情况。"],
            "insights": [],
            "based_on_public_records": 0,
            "updated_at": datetime.utcnow().isoformat(),
            "generator": "ollama_rag_v2",
        }
        return save_user_home_advice_payload(db, current_user, payload)

    recent_contexts = record_contexts[:3]
    trend_contexts = record_contexts[3:8]
    recent_records_text = "\n".join(
        f"- {ctx.created_at.strftime('%Y-%m-%d %H:%M')} | {ctx.title}: {truncate_text(ctx.summary, 180)}"
        for ctx in recent_contexts
    )
    trend_records_text = "\n".join(
        f"- {ctx.created_at.strftime('%Y-%m-%d %H:%M')} | {ctx.title}: {truncate_text(ctx.summary, 120)}"
        for ctx in trend_contexts
    )
    rag_context, _ = _rag_context(db, _home_advice_rag_query(profile_context, [ctx.summary for ctx in recent_contexts]))
    prompt = _home_advice_prompt(
        profile_context=profile_context,
        recent_records_text=recent_records_text,
        trend_records_text=trend_records_text,
        rag_context=rag_context,
    )
    home_options = {
        "temperature": min(settings.OLLAMA_TEMPERATURE, 0.2),
        "top_p": min(settings.OLLAMA_TOP_P, 0.85),
        "top_k": min(settings.OLLAMA_TOP_K, 30),
        "num_predict": min(settings.OLLAMA_NUM_PREDICT, 220),
    }
    try:
        raw_reply = await asyncio.to_thread(_call_ollama, _system_prompt(), prompt, home_options)
        llm_payload = _extract_json_block(raw_reply)
        final_payload = _normalize_home_advice_payload(llm_payload, based_on_public_records)
    except RuntimeError as exc:
        logger.warning("home advice generation failed user_id=%s: %s", current_user.id, exc)
        final_payload = {
            "summary": "首页 AI 个性化建议暂时生成失败，请稍后重新进入首页再试。",
            "recommendations": [],
            "insights": [],
            "based_on_public_records": based_on_public_records,
            "updated_at": datetime.utcnow().isoformat(),
            "generator": "llm_unavailable_v1",
        }
    return save_user_home_advice_payload(db, current_user, final_payload)


def _ollama_request(system_prompt: str, user_prompt: str, stream: bool, options_override: dict | None = None) -> urllib.request.Request:
    options = {
        "temperature": settings.OLLAMA_TEMPERATURE,
        "top_p": settings.OLLAMA_TOP_P,
        "top_k": settings.OLLAMA_TOP_K,
        "repeat_penalty": settings.OLLAMA_REPEAT_PENALTY,
        "num_predict": settings.OLLAMA_NUM_PREDICT,
    }
    if options_override:
        options.update({key: value for key, value in options_override.items() if value is not None})
    payload = {
        "model": settings.OLLAMA_MODEL,
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": stream,
        "think": not settings.OLLAMA_DISABLE_THINKING,
        "options": options,
    }
    return urllib.request.Request(
        url=f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )


def _call_ollama(system_prompt: str, user_prompt: str, options_override: dict | None = None) -> str:
    try:
        with urllib.request.urlopen(_ollama_request(system_prompt, user_prompt, False, options_override), timeout=settings.OLLAMA_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Ollama HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore') or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama 连接失败: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("Ollama 请求超时") from exc

    reply = _clean_response(payload.get("response", ""))
    if not reply:
        raise RuntimeError("Ollama 未返回有效内容")
    return reply


def _stream_ollama(system_prompt: str, user_prompt: str, options_override: dict | None = None):
    try:
        with urllib.request.urlopen(_ollama_request(system_prompt, user_prompt, True, options_override), timeout=settings.OLLAMA_TIMEOUT_SECONDS) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                chunk = _clean_response(item.get("response", ""))
                if chunk:
                    yield chunk
                if item.get("done"):
                    break
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Ollama HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore') or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama 连接失败: {exc.reason}") from exc
    except TimeoutError as exc:
        raise RuntimeError("Ollama 请求超时") from exc


async def _generate(
    *,
    user_message: str,
    current_user: models.User,
    db: Session,
    chat_id: Optional[int],
    health_context: str,
    rag_context: str,
    private_context: str,
) -> str:
    prompt = _prompt(
        user_message=user_message,
        profile_context=public_profile_summary(current_user),
        health_context=health_context,
        private_context=private_context,
        rag_context=rag_context,
        history_context=_chat_history(db, current_user.id, chat_id),
    )
    try:
        return await asyncio.to_thread(_call_ollama, _system_prompt(), prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"本地模型服务不可用：{exc}") from exc


def _save_ai_message(user_id: int, session_id: int, ai_reply: str) -> datetime:
    db = SessionLocal()
    try:
        ai_message = models.ChatMessage(
            user_id=user_id,
            session_id=session_id,
            message=ai_reply,
            is_user=False,
            created_at=datetime.utcnow(),
        )
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        return ai_message.created_at
    finally:
        db.close()


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _metrics(record: models.HealthData) -> dict:
    payload = json_loads_object(record.data_content)
    return payload.get("metrics") if isinstance(payload.get("metrics"), dict) else {}


@router.get("/private-context/options", response_model=schemas.AiPrivateContextOptionsResponse)
async def get_private_context_options(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_ai_service_enabled(db)
    return schemas.AiPrivateContextOptionsResponse(items=build_private_context_options(db, current_user))


@router.post("/chat", response_model=schemas.ChatResponse)
async def chat_with_ai(
    message: schemas.ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_ai_service_enabled(db)
    session_id = message.chat_id
    user_message = models.ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        message=message.message,
        is_user=True,
        created_at=datetime.utcnow(),
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    if not user_message.session_id:
        user_message.session_id = user_message.id
        db.commit()
        db.refresh(user_message)
    session_id = user_message.session_id

    health_context, public_context_count = build_public_health_context(db, current_user)
    private_context, private_count = build_private_context(db, current_user, message.selected_private_context_ids)
    rag_context, rag_refs = _rag_context(db, message.message)
    ai_reply = await _generate(
        user_message=message.message,
        current_user=current_user,
        db=db,
        chat_id=session_id,
        health_context=health_context,
        rag_context=rag_context,
        private_context=private_context,
    )

    ai_message = models.ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        message=ai_reply,
        is_user=False,
        created_at=datetime.utcnow(),
    )
    db.add(ai_message)
    db.commit()
    db.refresh(ai_message)

    return schemas.ChatResponse(
        reply=ai_reply,
        timestamp=ai_message.created_at,
        chat_id=session_id,
        references=rag_refs,
        personalization_used=bool(public_context_count or public_profile_summary(current_user) or private_count),
        private_context_used=private_count,
    )


@router.post("/chat/stream")
async def chat_with_ai_stream(
    message: schemas.ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_ai_service_enabled(db)
    session_id = message.chat_id
    user_message = models.ChatMessage(
        user_id=current_user.id,
        session_id=session_id,
        message=message.message,
        is_user=True,
        created_at=datetime.utcnow(),
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)
    if not user_message.session_id:
        user_message.session_id = user_message.id
        db.commit()
        db.refresh(user_message)
    session_id = user_message.session_id

    health_context, public_context_count = build_public_health_context(db, current_user)
    private_context, private_count = build_private_context(db, current_user, message.selected_private_context_ids)
    rag_context, rag_refs = _rag_context(db, message.message)
    chat_id = session_id
    prompt = _prompt(
        user_message=message.message,
        profile_context=public_profile_summary(current_user),
        health_context=health_context,
        private_context=private_context,
        rag_context=rag_context,
        history_context=_chat_history(db, current_user.id, session_id),
    )
    personalization_used = bool(public_context_count or public_profile_summary(current_user) or private_count)

    def event_stream():
        full_reply_parts: list[str] = []
        yield _sse(
            "meta",
            {
                "chat_id": chat_id,
                "references": rag_refs,
                "personalization_used": personalization_used,
                "private_context_used": private_count,
            },
        )
        if private_count:
            yield _sse("status", {"phase": "decrypting", "text": "正在读取并解密你选择的私密数据..."})
        if rag_refs:
            yield _sse("status", {"phase": "retrieving", "text": "正在检索知识库..."})
        if public_context_count:
            yield _sse("status", {"phase": "personalizing", "text": "正在整理你的公开健康数据..."})
        yield _sse("status", {"phase": "generating", "text": "正在生成回答..."})
        try:
            for chunk in _stream_ollama(_system_prompt(), prompt):
                full_reply_parts.append(chunk)
                yield _sse("delta", {"content": chunk})
            full_reply = "".join(full_reply_parts).strip()
            if not full_reply:
                raise RuntimeError("本地模型未返回有效内容")
            yield _sse("status", {"phase": "saving", "text": "正在保存对话..."})
            created_at = _save_ai_message(current_user.id, session_id, full_reply)
            yield _sse(
                "done",
                {
                    "reply": full_reply,
                    "timestamp": created_at.isoformat(),
                    "chat_id": chat_id,
                    "references": rag_refs,
                    "personalization_used": personalization_used,
                    "private_context_used": private_count,
                },
            )
        except RuntimeError as exc:
            yield _sse("error", {"detail": f"本地模型服务不可用：{exc}"})
        except Exception as exc:  # noqa: BLE001
            yield _sse("error", {"detail": f"流式输出失败：{exc}"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@router.get("/chat/history")
async def get_chat_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_ai_service_enabled(db)
    messages = (
        db.query(models.ChatMessage)
        .filter(
            models.ChatMessage.user_id == current_user.id,
            models.ChatMessage.session_id.isnot(None),
        )
        .order_by(models.ChatMessage.created_at.asc(), models.ChatMessage.id.asc())
        .all()
    )
    session_map: dict[int, dict] = {}
    for msg in messages:
        if msg.session_id not in session_map:
            session_map[msg.session_id] = {
                "id": msg.session_id,
                "title": f"对话 {msg.created_at.strftime('%m-%d')}",
                "last_message_time": msg.created_at,
                "message_count": 0,
            }
        session = session_map[msg.session_id]
        session["message_count"] += 1
        session["last_message_time"] = msg.created_at
        if msg.is_user and session["title"].startswith("对话 ") and (msg.message or "").strip():
            session["title"] = _history_session_title(msg)

    sessions = sorted(session_map.values(), key=lambda item: item["last_message_time"], reverse=True)
    return sessions


@router.get("/chat/{chat_id}/messages")
async def get_chat_messages(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_ai_service_enabled(db)
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == current_user.id, models.ChatMessage.session_id == chat_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
    return [
        {"id": msg.id, "message": msg.message, "is_user": msg.is_user, "created_at": msg.created_at}
        for msg in messages
    ]


@router.delete("/chat/{chat_id}")
async def delete_chat(
    chat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_ai_service_enabled(db)
    deleted_count = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.user_id == current_user.id, models.ChatMessage.session_id == chat_id)
        .delete()
    )
    db.commit()
    return {"message": f"已删除 {deleted_count} 条消息"}


@router.get("/recommendations/{user_id}")
async def get_health_recommendations(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_ai_service_enabled(db)
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权访问其他用户的建议")

    records = (
        db.query(models.HealthData)
        .filter(models.HealthData.user_id == user_id)
        .order_by(models.HealthData.created_at.desc())
        .limit(10)
        .all()
    )
    if not records:
        return {"recommendations": ["暂无健康数据，请先录入健康信息。"]}

    latest = _metrics(records[0])
    recommendations: list[str] = []
    systolic = latest.get("blood_pressure_systolic")
    diastolic = latest.get("blood_pressure_diastolic")
    if systolic is not None and diastolic is not None and (systolic > 140 or diastolic > 90):
        recommendations.append("你的血压偏高，建议减少盐分摄入并增加适量有氧运动。")
    if latest.get("heart_rate") is not None and latest["heart_rate"] > 100:
        recommendations.append("你的心率偏快，建议减少咖啡因摄入并保证充足睡眠。")
    if latest.get("blood_sugar") is not None and latest["blood_sugar"] > 6.1:
        recommendations.append("你的血糖偏高，建议控制精制碳水摄入并增加运动。")
    recommendations.extend(
        [
            "建议每天保持 7-8 小时睡眠。",
            "建议每周至少进行 150 分钟中等强度有氧运动。",
            "建议保持均衡饮食，适量增加蔬菜和优质蛋白。",
        ]
    )
    return {"recommendations": recommendations[:5]}


@router.get("/home-advice", response_model=schemas.AiHomeAdviceResponse)
async def get_home_health_advice(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_ai_service_enabled(db)
    payload = load_cached_home_advice(current_user)
    if (
        not payload
        or not isinstance(payload.get("recommendations"), list)
        or payload.get("generator") == "llm_unavailable_v1"
        or payload.get("generator") not in {"ollama_rag_v2", "llm_unavailable_v1"}
    ):
        payload = await _generate_home_advice_payload(db, current_user)
    return schemas.AiHomeAdviceResponse(
        summary=payload.get("summary") or "暂无建议",
        recommendations=payload.get("recommendations") or [],
        insights=payload.get("insights") or [],
        based_on_public_records=int(payload.get("based_on_public_records") or 0),
        updated_at=payload.get("updated_at"),
    )


@router.post("/analyze")
async def analyze_health_data(
    analysis_data: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _ensure_ai_service_enabled(db)
    user_id = analysis_data.get("user_id", current_user.id)
    if current_user.id != user_id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权分析其他用户的数据")

    records = (
        db.query(models.HealthData)
        .filter(models.HealthData.user_id == user_id)
        .order_by(models.HealthData.created_at.desc())
        .all()
    )
    if not records:
        return {"analysis": "暂无健康数据可供分析", "insights": []}

    insights: list[str] = []
    if records:
        latest_metrics = _metrics(records[0])
        insights.extend(metric_lines(latest_metrics))
    if len(records) >= 2:
        recent = _metrics(records[0])
        previous = _metrics(records[1])
        if recent.get("weight") is not None and previous.get("weight") is not None:
            change = recent["weight"] - previous["weight"]
            if abs(change) > 0.5:
                direction = "增加" if change > 0 else "减少"
                insights.append(f"体重变化：{direction} {abs(change):.1f} kg")

    score = calculate_health_score(records[0])
    insights.append(f"健康评分：{score}/100")
    return {
        "analysis": f"基于最近 {len(records)} 条健康数据记录进行分析。",
        "insights": insights,
        "health_score": score,
        "data_points": len(records),
    }


def calculate_health_score(health_record: models.HealthData) -> int:
    score = 100
    metrics = _metrics(health_record)
    systolic = metrics.get("blood_pressure_systolic")
    diastolic = metrics.get("blood_pressure_diastolic")
    if systolic is not None and diastolic is not None and (systolic > 140 or diastolic > 90):
        score -= 20
    if metrics.get("heart_rate") is not None and metrics["heart_rate"] > 100:
        score -= 15
    if metrics.get("blood_sugar") is not None and metrics["blood_sugar"] > 6.1:
        score -= 20
    if metrics.get("height") not in (None, 0) and metrics.get("weight") not in (None, 0):
        bmi = metrics["weight"] / ((metrics["height"] / 100) ** 2)
        if bmi > 30:
            score -= 20
        elif bmi > 25 or bmi < 18.5:
            score -= 10
    return max(0, score)
