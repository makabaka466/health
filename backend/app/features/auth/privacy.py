import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _build_server_fernet() -> Fernet:
    digest = hashlib.sha256((settings.SECRET_KEY or "").encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_sensitive_value(value: Optional[str]) -> Optional[str]:
    raw = (value or "").strip()
    if not raw:
        return None
    return _build_server_fernet().encrypt(raw.encode("utf-8")).decode("utf-8")


def decrypt_sensitive_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return _build_server_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("敏感数据解密失败") from exc


def hash_sensitive_value(value: Optional[str], *, lower: bool = False) -> Optional[str]:
    raw = (value or "").strip()
    if not raw:
        return None
    if lower:
        raw = raw.lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def shadow_email(value: Optional[str]) -> Optional[str]:
    digest = hash_sensitive_value(value, lower=True)
    if not digest:
        return None
    return f"user_{digest[:16]}@private.local"


def shadow_wallet_address(value: Optional[str]) -> Optional[str]:
    digest = hash_sensitive_value(value, lower=True)
    if not digest:
        return None
    return f"0x{digest[:40]}"


def shadow_social_open_id(value: Optional[str]) -> Optional[str]:
    digest = hash_sensitive_value(value, lower=True)
    if not digest:
        return None
    return f"shadow_{digest[:32]}"


def mask_email(value: Optional[str]) -> Optional[str]:
    raw = (value or "").strip()
    if not raw:
        return None
    if "@" not in raw:
        return raw
    local_part, domain = raw.split("@", 1)
    if len(local_part) <= 2:
        masked = f"{local_part[:1]}*"
    else:
        masked = f"{local_part[:2]}{'*' * min(len(local_part) - 2, 6)}"
    return f"{masked}@{domain}"


def mask_wallet_address(value: Optional[str]) -> Optional[str]:
    raw = (value or "").strip()
    if not raw:
        return None
    if len(raw) <= 12:
        return raw
    return f"{raw[:6]}...{raw[-4:]}"


def reveal_email(user) -> Optional[str]:
    encrypted = getattr(user, "encrypted_email", None)
    return decrypt_sensitive_value(encrypted) if encrypted else getattr(user, "email", None)


def reveal_wallet_address(user) -> Optional[str]:
    encrypted = getattr(user, "encrypted_wallet_address", None)
    return decrypt_sensitive_value(encrypted) if encrypted else getattr(user, "wallet_address", None)


def reveal_social_open_id(user) -> Optional[str]:
    encrypted = getattr(user, "encrypted_social_open_id", None)
    return decrypt_sensitive_value(encrypted) if encrypted else getattr(user, "social_open_id", None)


def apply_sensitive_user_fields(
    user,
    *,
    email: Optional[str] = None,
    wallet_address: Optional[str] = None,
    social_open_id: Optional[str] = None,
) -> None:
    if email is not None:
        user.email = shadow_email(email)
        user.encrypted_email = encrypt_sensitive_value(email)
        user.email_hash = hash_sensitive_value(email, lower=True)

    if wallet_address is not None:
        user.wallet_address = shadow_wallet_address(wallet_address)
        user.encrypted_wallet_address = encrypt_sensitive_value(wallet_address)
        user.wallet_address_hash = hash_sensitive_value(wallet_address, lower=True)

    if social_open_id is not None:
        user.social_open_id = shadow_social_open_id(social_open_id)
        user.encrypted_social_open_id = encrypt_sensitive_value(social_open_id)
        user.social_open_id_hash = hash_sensitive_value(social_open_id, lower=True)
