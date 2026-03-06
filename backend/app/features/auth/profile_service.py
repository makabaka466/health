from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
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
    def _resolve_private_key(user: models.User, provided_private_key: str | None) -> str:
        if provided_private_key:
            if not verify_user_private_key(provided_private_key, user.wallet_address, user.private_key_hash):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="私钥校验失败")
            return normalize_private_key(provided_private_key)

        if user.private_key_hash:
            # 身份已通过 JWT 校验时，允许使用当前用户的密钥哈希派生内部密钥，避免每次手动输入私钥。
            return normalize_private_key(user.private_key_hash)

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前账号未绑定可用私钥")

    def upsert_profile(self, user: models.User, profile_data: str, private_key: str | None, is_public: bool) -> dict:
        effective_private_key = self._resolve_private_key(user, private_key)

        user.encrypted_profile_data = encrypt_text(profile_data, effective_private_key)
        user.profile_is_public = is_public
        user.public_profile_data = profile_data if is_public else None

        self.db.commit()
        self.db.refresh(user)

        return {
            "user_id": user.id,
            "wallet_address": user.wallet_address,
            "profile_is_public": user.profile_is_public,
            "profile_data": user.public_profile_data if user.profile_is_public else None,
        }

    def get_my_profile(self, user: models.User, private_key: str | None = None) -> dict:
        profile_data = user.public_profile_data if user.profile_is_public else None
        if user.encrypted_profile_data:
            if user.profile_is_public and not private_key:
                return {
                    "user_id": user.id,
                    "wallet_address": user.wallet_address,
                    "profile_is_public": user.profile_is_public,
                    "profile_data": profile_data,
                }

            effective_private_key = self._resolve_private_key(user, private_key)

            try:
                profile_data = decrypt_text(user.encrypted_profile_data, effective_private_key)
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="当前资料需使用原始私钥解锁，请在请求中传入 private_key",
                ) from exc

        return {
            "user_id": user.id,
            "wallet_address": user.wallet_address,
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
            "wallet_address": target_user.wallet_address,
            "profile_is_public": True,
            "profile_data": target_user.public_profile_data,
        }
