import base64
import hashlib
from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session
from eth_account import Account

from app import models, schemas
from app.config import settings
from app.features.blockchain.encryption import normalize_private_key, private_key_hash


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
SOCIAL_TICKET_EXPIRE_MINUTES = 15
SUPPORTED_SOCIAL_PROVIDERS = {"wechat", "alipay"}


class AuthService:
    """认证服务：封装注册、登录、管理员校验等认证相关数据库操作。"""

    def __init__(self, db: Session):
        """初始化服务并注入当前请求的数据库会话。"""
        self.db = db

    @staticmethod
    def _build_server_fernet() -> Fernet:
        digest = hashlib.sha256((settings.SECRET_KEY or "").encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))

    @classmethod
    def encrypt_private_key_for_storage(cls, private_key: str) -> str:
        return cls._build_server_fernet().encrypt(normalize_private_key(private_key).encode("utf-8")).decode("utf-8")

    @classmethod
    def decrypt_private_key_from_storage(cls, encrypted_value: str) -> str:
        try:
            return cls._build_server_fernet().decrypt((encrypted_value or "").encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("私钥存储损坏，无法解密") from exc

    async def register(self, user: schemas.UserCreate) -> tuple[models.User, str]:
        """注册用户：支持普通用户与管理员（需管理员密钥）注册。"""
        existing_user = self.db.query(models.User).filter(models.User.username == user.username).first()
        if existing_user:
            raise ValueError("用户名已存在")

        existing_email = self.db.query(models.User).filter(models.User.email == user.email).first()
        if existing_email:
            raise ValueError("邮箱已存在")

        requested_role = "admin" if user.role == "admin" else "user"
        if requested_role == "admin" and user.admin_register_key != settings.ADMIN_REGISTER_KEY:
            raise ValueError("管理员密钥错误")

        return self._create_user_account(
            username=user.username,
            email=user.email,
            password=user.password,
            role=requested_role,
        )

    async def social_login_init(self, payload: schemas.SocialLoginInitRequest) -> dict:
        provider = self._normalize_social_provider(payload.provider)
        open_id, nickname = self._resolve_social_identity(provider, payload.auth_code, payload.nickname)

        user = (
            self.db.query(models.User)
            .filter(models.User.social_provider == provider, models.User.social_open_id == open_id)
            .first()
        )
        if user:
            return {
                "need_profile_completion": False,
                "user": user,
            }

        social_ticket = self._build_social_ticket(provider=provider, open_id=open_id, nickname=nickname)
        suggested_prefix = "wx" if provider == "wechat" else "ali"
        suggested_username = f"{suggested_prefix}_{open_id[-6:]}"
        return {
            "need_profile_completion": True,
            "social_ticket": social_ticket,
            "social_provider": provider,
            "social_nickname": nickname,
            "suggested_username": suggested_username,
        }

    async def complete_social_profile(self, payload: schemas.SocialProfileCompleteRequest) -> tuple[models.User, str]:
        provider, open_id, nickname = self._parse_social_ticket(payload.social_ticket)

        existing_bind = (
            self.db.query(models.User)
            .filter(models.User.social_provider == provider, models.User.social_open_id == open_id)
            .first()
        )
        if existing_bind:
            raise ValueError("该第三方账号已绑定系统用户，请直接使用第三方登录")

        return self._create_user_account(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            role="user",
            social_provider=provider,
            social_open_id=open_id,
            social_nickname=nickname,
        )

    def _create_user_account(
        self,
        username: str,
        email: str,
        password: str,
        role: str = "user",
        social_provider: str | None = None,
        social_open_id: str | None = None,
        social_nickname: str | None = None,
    ) -> tuple[models.User, str]:
        existing_user = self.db.query(models.User).filter(models.User.username == username).first()
        if existing_user:
            raise ValueError("用户名已存在")

        existing_email = self.db.query(models.User).filter(models.User.email == email).first()
        if existing_email:
            raise ValueError("邮箱已存在")

        role_description = "系统管理员" if role == "admin" else "普通用户"
        role_ref = self._get_or_create_role(role, role_description)

        account = Account.create()
        generated_private_key = normalize_private_key(account.key.hex())

        db_user = models.User(
            username=username,
            email=email,
            password_hash=self.hash_password(password),
            wallet_address=account.address,
            private_key_hash=private_key_hash(generated_private_key),
            encrypted_private_key=self.encrypt_private_key_for_storage(generated_private_key),
            social_provider=social_provider,
            social_open_id=social_open_id,
            social_nickname=social_nickname,
            role=role,
            role_id=role_ref.id,
            is_active=True,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user, generated_private_key

    @staticmethod
    def _normalize_social_provider(provider: str) -> str:
        normalized = (provider or "").strip().lower()
        mapping = {
            "wx": "wechat",
            "wechat": "wechat",
            "weixin": "wechat",
            "ali": "alipay",
            "alipay": "alipay",
            "zhifubao": "alipay",
        }
        resolved = mapping.get(normalized)
        if resolved not in SUPPORTED_SOCIAL_PROVIDERS:
            raise ValueError("暂不支持该第三方登录渠道")
        return resolved

    @staticmethod
    def _resolve_social_identity(provider: str, auth_code: str | None, nickname: str | None) -> tuple[str, str]:
        code = (auth_code or f"demo_{provider}").strip()
        digest = hashlib.sha256(f"{provider}:{code}".encode("utf-8")).hexdigest()
        open_id = digest[:32]
        default_nickname = f"{('微信' if provider == 'wechat' else '支付宝')}用户{digest[-4:]}"
        return open_id, (nickname or default_nickname)

    @staticmethod
    def _build_social_ticket(provider: str, open_id: str, nickname: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=SOCIAL_TICKET_EXPIRE_MINUTES)
        payload = {
            "typ": "social_ticket",
            "provider": provider,
            "open_id": open_id,
            "nickname": nickname,
            "exp": expire,
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def _parse_social_ticket(ticket: str) -> tuple[str, str, str]:
        try:
            payload = jwt.decode(ticket, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if payload.get("typ") != "social_ticket":
                raise ValueError("无效的第三方登录凭证")
            provider = str(payload.get("provider") or "")
            open_id = str(payload.get("open_id") or "")
            nickname = str(payload.get("nickname") or "")
            if not provider or not open_id:
                raise ValueError("第三方登录凭证缺少必要字段")
            return provider, open_id, nickname
        except JWTError as exc:
            raise ValueError("第三方登录凭证已失效，请重新登录") from exc

    async def authenticate(self, username: str, password: str) -> models.User | None:
        """用户名密码认证：成功返回用户对象，失败返回 None。"""
        user = self.db.query(models.User).filter(models.User.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        
        return user

    async def authenticate_admin(self, username: str, password: str) -> models.User | None:
        """管理员认证：在普通认证成功后，额外校验身份是否为 admin。"""
        user = await self.authenticate(username, password)
        user_role = user.role_ref.name if user and user.role_ref else user.role if user else None
        if not user or user_role not in {"admin", "super_admin"}:
            return None
        return user

    async def get_user_by_username(self, username: str) -> models.User | None:
        """按用户名查询用户，用于 token 反查当前登录人。"""
        return self.db.query(models.User).filter(models.User.username == username).first()

    def reveal_private_key(self, user: models.User, password: str) -> str:
        if not self.verify_password(password, user.password_hash):
            raise ValueError("密码错误")

        if not user.encrypted_private_key:
            raise ValueError("当前账号暂不支持查看私钥，请使用注册时保存的私钥")

        return self.decrypt_private_key_from_storage(user.encrypted_private_key)

    def _get_or_create_role(self, role_name: str, description: str) -> models.Role:
        """获取或创建身份记录（roles 表），避免注册时缺少 role。"""
        role_ref = self.db.query(models.Role).filter(models.Role.name == role_name).first()
        if role_ref:
            return role_ref

        role_ref = models.Role(name=role_name, description=description)
        self.db.add(role_ref)
        self.db.flush()
        return role_ref

    @staticmethod
    def hash_password(password: str) -> str:
        """对明文密码做哈希存储，避免数据库保存明文密码。"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """校验用户输入密码与数据库哈希是否匹配。"""
        if not hashed_password:
            return False
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except (UnknownHashError, ValueError, TypeError):
            return False


def ensure_admin_user(db: Session) -> None:
    """系统启动时同步基础身份与种子账号，便于开箱即用。"""
    role_definitions = {
        "admin": "系统管理员",
        "user": "普通用户",
    }

    role_map: dict[str, models.Role] = {}
    for role_name, description in role_definitions.items():
        role_ref = db.query(models.Role).filter(models.Role.name == role_name).first()
        if not role_ref:
            role_ref = models.Role(name=role_name, description=description)
            db.add(role_ref)
            db.flush()
        role_map[role_name] = role_ref

    seed_users = [
        {
            "username": settings.ADMIN_USERNAME,
            "email": settings.ADMIN_EMAIL,
            "password": settings.ADMIN_PASSWORD,
            "role": "admin",
        },
        {
            "username": "xiaoming",
            "email": "xiaoming@health.com",
            "password": "123456",
            "role": "user",
        },
        {
            "username": "xiaohong",
            "email": "xiaohong@health.com",
            "password": "123456",
            "role": "user",
        },
    ]

    for user_item in seed_users:
        existing_user = db.query(models.User).filter(models.User.username == user_item["username"]).first()
        if existing_user:
            existing_user.role = user_item["role"]
            existing_user.role_id = role_map[user_item["role"]].id
            existing_user.email = user_item["email"]
            existing_user.is_active = True

            if not AuthService.verify_password(user_item["password"], existing_user.password_hash):
                existing_user.password_hash = AuthService.hash_password(user_item["password"])
            continue

        db.add(
            models.User(
                username=user_item["username"],
                email=user_item["email"],
                password_hash=AuthService.hash_password(user_item["password"]),
                role=user_item["role"],
                role_id=role_map[user_item["role"]].id,
                is_active=True,
            )
        )

    db.commit()
