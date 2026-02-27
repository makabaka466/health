from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings


pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class AuthService:
    """认证服务：封装注册、登录、管理员校验等认证相关数据库操作。"""

    def __init__(self, db: Session):
        """初始化服务并注入当前请求的数据库会话。"""
        self.db = db

    async def register(self, user: schemas.UserCreate) -> models.User:
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

        role_description = "系统管理员" if requested_role == "admin" else "普通用户"
        role_ref = self._get_or_create_role(requested_role, role_description)

        db_user = models.User(
            username=user.username,
            email=user.email,
            password_hash=self.hash_password(user.password),
            role=requested_role,
            role_id=role_ref.id,
            is_active=True,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user

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
