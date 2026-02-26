import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.routers.auth import get_current_user


router = APIRouter()


def _parse_tags(raw_tags: Optional[str]) -> List[str]:
    if not raw_tags:
        return []

    try:
        parsed = json.loads(raw_tags)
        if isinstance(parsed, list):
            return [str(tag) for tag in parsed if str(tag).strip()]
    except (json.JSONDecodeError, TypeError):
        pass

    return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]


def _join_tags(tags: Optional[List[str]]) -> str:
    return json.dumps(tags or [], ensure_ascii=False)


def _favorite_count_map(db: Session, article_ids: List[int]) -> dict[int, int]:
    if not article_ids:
        return {}

    rows = (
        db.query(models.ArticleFavorite.article_id, func.count(models.ArticleFavorite.id))
        .filter(models.ArticleFavorite.article_id.in_(article_ids))
        .group_by(models.ArticleFavorite.article_id)
        .all()
    )
    return {article_id: count for article_id, count in rows}


def _to_article_response(article: models.HealthArticle, favorite_count: int = 0) -> schemas.HealthArticleResponse:
    return schemas.HealthArticleResponse(
        id=article.id,
        title=article.title,
        category=article.category,
        summary=article.summary,
        content=article.content,
        cover_image=article.cover_image,
        tags=_parse_tags(article.tags),
        view_count=article.view_count,
        favorite_count=favorite_count,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


def _assert_category(category: str) -> None:
    if category not in schemas.ARTICLE_CATEGORIES:
        raise HTTPException(status_code=400, detail="无效的文章分类")


def _assert_admin(user: models.User) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可操作")


def _record_read_history(db: Session, user_id: int, article_id: int) -> None:
    history = (
        db.query(models.ArticleReadHistory)
        .filter(
            models.ArticleReadHistory.user_id == user_id,
            models.ArticleReadHistory.article_id == article_id,
        )
        .first()
    )

    if history:
        history.read_count += 1
        history.last_read_at = datetime.utcnow()
    else:
        db.add(
            models.ArticleReadHistory(
                user_id=user_id,
                article_id=article_id,
                read_count=1,
                last_read_at=datetime.utcnow(),
            )
        )


@router.get("/articles", response_model=schemas.HealthArticleListResponse)
async def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    sort_by: str = Query("latest", pattern="^(latest|hot)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.HealthArticle)

    if category:
        query = query.filter(models.HealthArticle.category == category)

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                models.HealthArticle.title.ilike(like),
                models.HealthArticle.summary.ilike(like),
                models.HealthArticle.content.ilike(like),
            )
        )

    total = query.count()

    if sort_by == "hot":
        query = query.order_by(desc(models.HealthArticle.view_count), desc(models.HealthArticle.created_at))
    else:
        query = query.order_by(desc(models.HealthArticle.created_at))

    articles = query.offset((page - 1) * page_size).limit(page_size).all()
    article_ids = [article.id for article in articles]
    count_map = _favorite_count_map(db, article_ids)

    return schemas.HealthArticleListResponse(
        items=[_to_article_response(article, count_map.get(article.id, 0)) for article in articles],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/articles/{article_id}", response_model=schemas.HealthArticleResponse)
async def get_article_detail(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    article = db.query(models.HealthArticle).filter(models.HealthArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.view_count += 1
    _record_read_history(db, current_user.id, article_id)
    db.commit()
    db.refresh(article)

    count_map = _favorite_count_map(db, [article.id])
    return _to_article_response(article, count_map.get(article.id, 0))


@router.post("/articles/{article_id}/favorite", response_model=schemas.FavoriteResponse)
async def favorite_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    article = db.query(models.HealthArticle).filter(models.HealthArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    existing = (
        db.query(models.ArticleFavorite)
        .filter(
            models.ArticleFavorite.user_id == current_user.id,
            models.ArticleFavorite.article_id == article_id,
        )
        .first()
    )
    if not existing:
        db.add(models.ArticleFavorite(user_id=current_user.id, article_id=article_id))
        db.commit()

    return schemas.FavoriteResponse(article_id=article_id, is_favorited=True)


@router.delete("/articles/{article_id}/favorite", response_model=schemas.FavoriteResponse)
async def unfavorite_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    favorite = (
        db.query(models.ArticleFavorite)
        .filter(
            models.ArticleFavorite.user_id == current_user.id,
            models.ArticleFavorite.article_id == article_id,
        )
        .first()
    )

    if favorite:
        db.delete(favorite)
        db.commit()

    return schemas.FavoriteResponse(article_id=article_id, is_favorited=False)


@router.get("/favorites", response_model=schemas.HealthArticleListResponse)
async def list_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    favorites_query = db.query(models.ArticleFavorite).filter(models.ArticleFavorite.user_id == current_user.id)
    total = favorites_query.count()

    favorites = (
        favorites_query.order_by(desc(models.ArticleFavorite.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    articles = [favorite.article for favorite in favorites if favorite.article]
    article_ids = [article.id for article in articles]
    count_map = _favorite_count_map(db, article_ids)

    return schemas.HealthArticleListResponse(
        items=[_to_article_response(article, count_map.get(article.id, 0)) for article in articles],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/read-history", response_model=List[schemas.ReadingHistoryResponse])
async def list_read_history(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    rows = (
        db.query(models.ArticleReadHistory)
        .filter(models.ArticleReadHistory.user_id == current_user.id)
        .order_by(desc(models.ArticleReadHistory.last_read_at))
        .limit(limit)
        .all()
    )

    return [
        schemas.ReadingHistoryResponse(
            article_id=row.article_id,
            article_title=row.article.title if row.article else "",
            category=row.article.category if row.article else "",
            last_read_at=row.last_read_at,
            read_count=row.read_count,
        )
        for row in rows
        if row.article
    ]


@router.get("/recommendations/home", response_model=schemas.HomepageRecommendationResponse)
async def get_home_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    hot_articles = (
        db.query(models.HealthArticle)
        .order_by(desc(models.HealthArticle.view_count), desc(models.HealthArticle.created_at))
        .limit(6)
        .all()
    )
    latest_articles = db.query(models.HealthArticle).order_by(desc(models.HealthArticle.created_at)).limit(6).all()

    ids = list({article.id for article in hot_articles + latest_articles})
    count_map = _favorite_count_map(db, ids)

    return schemas.HomepageRecommendationResponse(
        hot_articles=[_to_article_response(article, count_map.get(article.id, 0)) for article in hot_articles],
        latest_articles=[_to_article_response(article, count_map.get(article.id, 0)) for article in latest_articles],
    )


@router.post("/admin/articles", response_model=schemas.HealthArticleResponse)
async def create_article(
    payload: schemas.HealthArticleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _assert_admin(current_user)
    _assert_category(payload.category)

    article = models.HealthArticle(
        title=payload.title,
        category=payload.category,
        summary=payload.summary,
        content=payload.content,
        cover_image=payload.cover_image,
        tags=_join_tags(payload.tags),
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return _to_article_response(article, 0)


@router.put("/admin/articles/{article_id}", response_model=schemas.HealthArticleResponse)
async def update_article(
    article_id: int,
    payload: schemas.HealthArticleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _assert_admin(current_user)

    article = db.query(models.HealthArticle).filter(models.HealthArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    update_data = payload.model_dump(exclude_unset=True)
    if "category" in update_data and update_data["category"]:
        _assert_category(update_data["category"])

    if "tags" in update_data:
        update_data["tags"] = _join_tags(update_data["tags"]) if update_data["tags"] is not None else _join_tags([])

    for key, value in update_data.items():
        setattr(article, key, value)

    db.commit()
    db.refresh(article)

    count_map = _favorite_count_map(db, [article.id])
    return _to_article_response(article, count_map.get(article.id, 0))


@router.delete("/admin/articles/{article_id}")
async def delete_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _assert_admin(current_user)

    article = db.query(models.HealthArticle).filter(models.HealthArticle.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    db.delete(article)
    db.commit()
    return {"message": "文章已删除"}
