import base64
import hashlib
from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from eth_account import Account
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings
from app.features.auth.privacy import (
    apply_sensitive_user_fields,
    hash_sensitive_value,
    mask_email,
    mask_wallet_address,
    reveal_email,
    reveal_social_open_id,
    reveal_wallet_address,
)
from app.features.blockchain.service import chain_service
from app.features.blockchain.encryption import normalize_private_key, private_key_hash


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
SOCIAL_TICKET_EXPIRE_MINUTES = 15
SUPPORTED_SOCIAL_PROVIDERS = {"wechat", "alipay"}


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _build_server_fernet() -> Fernet:
        digest = hashlib.sha256((settings.SECRET_KEY or "").encode("utf-8")).digest()
        return Fernet(base64.urlsafe_b64encode(digest))

    @staticmethod
    def email_hash(email: str | None) -> str | None:
        return hash_sensitive_value(email, lower=True)

    @staticmethod
    def wallet_hash(wallet_address: str | None) -> str | None:
        return hash_sensitive_value(wallet_address, lower=True)

    @staticmethod
    def social_open_id_hash(open_id: str | None) -> str | None:
        return hash_sensitive_value(open_id, lower=True)

    @classmethod
    def encrypt_private_key_for_storage(cls, private_key: str) -> str:
        return cls._build_server_fernet().encrypt(normalize_private_key(private_key).encode("utf-8")).decode("utf-8")

    @classmethod
    def decrypt_private_key_from_storage(cls, encrypted_value: str) -> str:
        try:
            return cls._build_server_fernet().decrypt((encrypted_value or "").encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("私钥存储损坏，无法解密") from exc

    def _get_user_by_email(self, email: str | None) -> models.User | None:
        email_hash = self.email_hash(email)
        if email_hash:
            matched = self.db.query(models.User).filter(models.User.email_hash == email_hash).first()
            if matched:
                return matched
        if email:
            return self.db.query(models.User).filter(models.User.email == email).first()
        return None

    def _get_user_by_social_identity(self, provider: str, open_id: str) -> models.User | None:
        open_id_hash = self.social_open_id_hash(open_id)
        if open_id_hash:
            matched = (
                self.db.query(models.User)
                .filter(models.User.social_provider == provider, models.User.social_open_id_hash == open_id_hash)
                .first()
            )
            if matched:
                return matched
        return (
            self.db.query(models.User)
            .filter(models.User.social_provider == provider, models.User.social_open_id == open_id)
            .first()
        )

    async def register(self, user: schemas.UserCreate) -> tuple[models.User, str, dict]:
        existing_user = self.db.query(models.User).filter(models.User.username == user.username).first()
        if existing_user:
            raise ValueError("用户名已存在")

        existing_email = self._get_user_by_email(user.email)
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

        user = self._get_user_by_social_identity(provider, open_id)
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

    async def complete_social_profile(self, payload: schemas.SocialProfileCompleteRequest) -> tuple[models.User, str, dict]:
        provider, open_id, nickname = self._parse_social_ticket(payload.social_ticket)

        existing_bind = self._get_user_by_social_identity(provider, open_id)
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
    ) -> tuple[models.User, str, dict]:
        existing_user = self.db.query(models.User).filter(models.User.username == username).first()
        if existing_user:
            raise ValueError("用户名已存在")

        existing_email = self._get_user_by_email(email)
        if existing_email:
            raise ValueError("邮箱已存在")

        role_description = "系统管理员" if role == "admin" else "普通用户"
        role_ref = self._get_or_create_role(role, role_description)

        account = Account.create()
        generated_private_key = normalize_private_key(account.key.hex())

        db_user = models.User(
            username=username,
            email="placeholder@private.local",
            password_hash=self.hash_password(password),
            wallet_address=None,
            private_key_hash=private_key_hash(generated_private_key),
            encrypted_private_key=self.encrypt_private_key_for_storage(generated_private_key),
            social_provider=social_provider,
            social_nickname=social_nickname,
            role=role,
            role_id=role_ref.id,
            is_active=True,
        )
        apply_sensitive_user_fields(
            db_user,
            email=email,
            wallet_address=account.address,
            social_open_id=social_open_id,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        faucet_result = self._auto_fund_wallet(account.address)
        return db_user, generated_private_key, faucet_result

    @staticmethod
    def _auto_fund_wallet(wallet_address: str) -> dict:
        result = {
            "faucet_enabled": bool(settings.WEB3_AUTO_FUND_NEW_USERS),
            "faucet_status": "disabled" if not settings.WEB3_AUTO_FUND_NEW_USERS else "pending",
            "faucet_amount_eth": settings.WEB3_AUTO_FUND_AMOUNT_ETH if settings.WEB3_AUTO_FUND_NEW_USERS else None,
            "faucet_tx_hash": None,
            "wallet_balance_eth": None,
            "faucet_error": None,
        }

        if not settings.WEB3_AUTO_FUND_NEW_USERS:
            return result

        if not chain_service.rpc_connected:
            result["faucet_status"] = "unavailable"
            result["faucet_error"] = "Ganache RPC is not connected"
            return result

        try:
            funding = chain_service.grant_test_eth(wallet_address, amount_eth=settings.WEB3_AUTO_FUND_AMOUNT_ETH)
            if not funding:
                result["faucet_status"] = "unavailable"
                result["faucet_error"] = "Faucet transaction was not sent"
                return result

            result["faucet_status"] = "success" if funding.get("status") == 1 else "failed"
            result["faucet_tx_hash"] = funding.get("tx_hash")
            result["wallet_balance_eth"] = funding.get("wallet_balance_eth")
            if result["faucet_status"] != "success":
                result["faucet_error"] = "Faucet transaction reverted"
            return result
        except Exception as exc:  # noqa: BLE001
            result["faucet_status"] = "failed"
            result["faucet_error"] = str(exc)
            return result

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
        user = self.db.query(models.User).filter(models.User.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    async def authenticate_admin(self, username: str, password: str) -> models.User | None:
        user = await self.authenticate(username, password)
        user_role = user.role_ref.name if user and user.role_ref else user.role if user else None
        if not user or user_role not in {"admin", "super_admin"}:
            return None
        return user

    async def get_user_by_username(self, username: str) -> models.User | None:
        return self.db.query(models.User).filter(models.User.username == username).first()

    @staticmethod
    def get_user_email(user: models.User) -> str | None:
        return reveal_email(user)

    @staticmethod
    def get_user_wallet_address(user: models.User) -> str | None:
        return reveal_wallet_address(user)

    @staticmethod
    def get_user_social_open_id(user: models.User) -> str | None:
        return reveal_social_open_id(user)

    @classmethod
    def serialize_user_response(cls, user: models.User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": mask_email(cls.get_user_email(user)),
            "role": user.role,
            "is_active": user.is_active,
            "wallet_address": mask_wallet_address(cls.get_user_wallet_address(user)),
            "created_at": user.created_at,
        }

    @classmethod
    def serialize_admin_user_response(cls, user: models.User) -> dict:
        return {
            "id": user.id,
            "username": user.username,
            "email": mask_email(cls.get_user_email(user)),
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }

    @classmethod
    def migrate_legacy_user_sensitive_fields(cls, user: models.User) -> bool:
        changed = False

        if user.email and not getattr(user, "email_hash", None):
            apply_sensitive_user_fields(user, email=user.email)
            changed = True

        if user.wallet_address and not getattr(user, "wallet_address_hash", None):
            apply_sensitive_user_fields(user, wallet_address=user.wallet_address)
            changed = True

        if user.social_open_id and not getattr(user, "social_open_id_hash", None):
            apply_sensitive_user_fields(user, social_open_id=user.social_open_id)
            changed = True

        return changed

    @classmethod
    def migrate_all_users_sensitive_fields(cls, db: Session) -> None:
        changed = False
        for user in db.query(models.User).all():
            if cls.migrate_legacy_user_sensitive_fields(user):
                changed = True
        if changed:
            db.commit()

    def reveal_private_key(self, user: models.User, password: str) -> str:
        if not self.verify_password(password, user.password_hash):
            raise ValueError("密码错误")

        if not user.encrypted_private_key:
            raise ValueError("当前账号暂不支持查看私钥，请使用注册时保存的私钥")

        return self.decrypt_private_key_from_storage(user.encrypted_private_key)

    def _get_or_create_role(self, role_name: str, description: str) -> models.Role:
        role_ref = self.db.query(models.Role).filter(models.Role.name == role_name).first()
        if role_ref:
            return role_ref

        role_ref = models.Role(name=role_name, description=description)
        self.db.add(role_ref)
        self.db.flush()
        return role_ref

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if not hashed_password:
            return False
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except (UnknownHashError, ValueError, TypeError):
            return False


def ensure_admin_user(db: Session) -> None:
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
            existing_user.is_active = True
            apply_sensitive_user_fields(existing_user, email=user_item["email"])

            if not AuthService.verify_password(user_item["password"], existing_user.password_hash):
                existing_user.password_hash = AuthService.hash_password(user_item["password"])
            continue

        db_user = models.User(
            username=user_item["username"],
            email="placeholder@private.local",
            password_hash=AuthService.hash_password(user_item["password"]),
            role=user_item["role"],
            role_id=role_map[user_item["role"]].id,
            is_active=True,
        )
        apply_sensitive_user_fields(db_user, email=user_item["email"])
        db.add(db_user)

    db.commit()
    AuthService.migrate_all_users_sensitive_fields(db)
