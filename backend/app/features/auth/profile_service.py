from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.features.ai.service import invalidate_user_home_advice
from app.features.auth.privacy import mask_wallet_address
from app.features.auth.service import AuthService
from app.features.blockchain.encryption import (
    decrypt_text,
    encrypt_text,
    normalize_private_key,
    verify_user_private_key,
)


class UserProfileService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _masked_wallet(user: models.User) -> str | None:
        return mask_wallet_address(AuthService.get_user_wallet_address(user))

    @staticmethod
    def _resolve_private_key(user: models.User, provided_private_key: str | None) -> str:
        real_wallet_address = AuthService.get_user_wallet_address(user)
        if provided_private_key:
            if not verify_user_private_key(provided_private_key, real_wallet_address, user.private_key_hash):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="私钥校验失败")
            return normalize_private_key(provided_private_key)

        if user.private_key_hash:
            return normalize_private_key(user.private_key_hash)

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前账号未绑定可用私钥")

    def upsert_profile(self, user: models.User, profile_data: str, private_key: str | None, is_public: bool) -> dict:
        effective_private_key = self._resolve_private_key(user, private_key)
        was_public = bool(user.profile_is_public)

        user.encrypted_profile_data = encrypt_text(profile_data, effective_private_key)
        user.profile_is_public = is_public
        user.public_profile_data = profile_data if is_public else None

        self.db.commit()
        self.db.refresh(user)
        if was_public or is_public:
            invalidate_user_home_advice(self.db, user)

        return {
            "user_id": user.id,
            "wallet_address": self._masked_wallet(user),
            "profile_is_public": user.profile_is_public,
            "profile_data": user.public_profile_data if user.profile_is_public else None,
        }

    def get_my_profile(self, user: models.User, private_key: str | None = None) -> dict:
        profile_data = user.public_profile_data if user.profile_is_public else None
        if user.encrypted_profile_data:
            if user.profile_is_public and not private_key:
                return {
                    "user_id": user.id,
                    "wallet_address": self._masked_wallet(user),
                    "profile_is_public": user.profile_is_public,
                    "profile_data": profile_data,
                }

            effective_private_key = self._resolve_private_key(user, private_key)
            try:
                profile_data = decrypt_text(user.encrypted_profile_data, effective_private_key)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="当前资料需要原始私钥解锁，请在请求中传入 private_key",
                ) from exc

        return {
            "user_id": user.id,
            "wallet_address": self._masked_wallet(user),
            "profile_is_public": user.profile_is_public,
            "profile_data": profile_data,
        }

    def get_public_profile(self, user_id: int) -> dict:
        target_user = self.db.query(models.User).filter(models.User.id == user_id).first()
        if not target_user or not target_user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

        if not target_user.profile_is_public:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该用户资料为私密状态")

        return {
            "user_id": target_user.id,
            "wallet_address": self._masked_wallet(target_user),
            "profile_is_public": True,
            "profile_data": target_user.public_profile_data,
        }
