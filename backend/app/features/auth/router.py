import json
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.config import settings
from app.database import get_db
from app import models
from app.features.auth.dependencies import create_access_token, get_current_admin, get_current_user
from app.schemas import (
    AdminUserListResponse,
    AdminUserResponse,
    SocialLoginInitRequest,
    SocialLoginInitResponse,
    SocialProfileCompleteRequest,
    Token,
    UserCreate,
    UserPrivateKeyRevealRequest,
    UserPrivateKeyRevealResponse,
    UserProfileResponse,
    UserProfileUpsertRequest,
    UserRegisterResponse,
    UserResponse,
)
from app.features.auth.service import AuthService
from app.features.auth.profile_service import UserProfileService

router = APIRouter()


def _get_bool_system_setting(db: Session, key: str, default_value: bool) -> bool:
    row = db.query(models.SystemSetting).filter(models.SystemSetting.setting_key == key).first()
    if not row:
        return default_value
    try:
        value = json.loads(row.setting_value)
        return bool(value)
    except Exception:  # noqa: BLE001
        return default_value


def _build_login_token(user: models.User) -> dict:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
    }

@router.post("/register", response_model=UserRegisterResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册接口：创建普通用户账号并返回基础资料。"""
    if not _get_bool_system_setting(db, "allow_user_register", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前系统已关闭用户注册")

    auth_service = AuthService(db)
    try:
        db_user, generated_private_key = await auth_service.register(user)
        return {
            **UserResponse.model_validate(db_user).model_dump(),
            "generated_private_key": generated_private_key,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录接口：校验账号密码并签发 JWT 令牌。"""
    auth_service = AuthService(db)
    user = await auth_service.authenticate(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    
    return _build_login_token(user)


@router.post("/social/login-init", response_model=SocialLoginInitResponse)
async def social_login_init(payload: SocialLoginInitRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        result = await auth_service.social_login_init(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if result.get("need_profile_completion"):
        return SocialLoginInitResponse(
            need_profile_completion=True,
            social_ticket=result.get("social_ticket"),
            social_provider=result.get("social_provider"),
            social_nickname=result.get("social_nickname"),
            suggested_username=result.get("suggested_username"),
        )

    user = result["user"]
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")

    token_payload = _build_login_token(user)
    return SocialLoginInitResponse(need_profile_completion=False, **token_payload)


@router.post("/social/complete", response_model=Token)
async def social_profile_complete(payload: SocialProfileCompleteRequest, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        user, _generated_private_key = await auth_service.complete_social_profile(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _build_login_token(user)

@router.post("/admin/login", response_model=Token)
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """管理员登录接口：要求账号身份为 admin 才可登录后台。"""
    auth_service = AuthService(db)
    user = await auth_service.authenticate_admin(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理员账号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data={"sub": user.username, "role": "admin"}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "role": user.role,
    }

@router.post("/me/profile", response_model=UserProfileResponse)
async def upsert_my_profile(
    payload: UserProfileUpsertRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    service = UserProfileService(db)
    return service.upsert_profile(
        user=current_user,
        profile_data=payload.profile_data,
        private_key=payload.private_key,
        is_public=payload.is_public,
    )


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_my_profile(
    private_key: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    service = UserProfileService(db)
    return service.get_my_profile(user=current_user, private_key=private_key)


@router.get("/profiles/{user_id}", response_model=UserProfileResponse)
async def get_user_public_profile(user_id: int, db: Session = Depends(get_db)):
    service = UserProfileService(db)
    return service.get_public_profile(user_id)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: models.User = Depends(get_current_user)):
    """当前用户接口：返回当前登录用户信息。"""
    return current_user


@router.post("/me/private-key", response_model=UserPrivateKeyRevealResponse)
async def reveal_my_private_key(
    payload: UserPrivateKeyRevealRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    auth_service = AuthService(db)
    try:
        private_key = auth_service.reveal_private_key(current_user, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"private_key": private_key}


@router.get("/admin/users", response_model=AdminUserListResponse)
async def list_admin_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str = Query(""),
    status_filter: str = Query("", alias="status"),
    role: str = Query(""),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    query = db.query(models.User)

    if keyword:
        like_pattern = f"%{keyword.strip()}%"
        query = query.filter(
            (models.User.username.ilike(like_pattern))
            | (models.User.email.ilike(like_pattern))
        )

    if status_filter == "active":
        query = query.filter(models.User.is_active.is_(True))
    elif status_filter == "disabled":
        query = query.filter(models.User.is_active.is_(False))

    if role:
        query = query.filter(models.User.role == role)

    total = query.count()
    items = (
        query.order_by(models.User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return AdminUserListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/admin/users/{user_id}", response_model=AdminUserResponse)
async def get_admin_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


@router.patch("/admin/users/{user_id}/status", response_model=AdminUserResponse)
async def update_admin_user_status(
    user_id: int,
    is_active: bool,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    if user.id == current_admin.id and not is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能禁用当前管理员账号")

    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


@router.post("/admin/users/{user_id}/reset-password")
async def reset_admin_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_admin),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user.password_hash = AuthService.hash_password("123456")
    db.commit()
    return {"message": f"用户 {user.username} 密码已重置为初始密码", "initial_password": "123456"}
