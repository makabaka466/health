import base64
import hashlib
import json
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from eth_account import Account

# 工具函数：标准化私钥格式
# 将输入的私钥字符串标准化。
# 处理空值或仅包含空格的情况
def normalize_private_key(private_key: str) -> str:
    key = (private_key or "").strip()
    if not key:
        raise ValueError("私钥不能为空")
    return key if key.startswith("0x") else f"0x{key}"

# 将私钥转换为对应的以太坊钱包地址。
# 利用 eth_account 库从私钥推导公钥并生成地址。
def private_key_to_address(private_key: str) -> str:
    normalized_key = normalize_private_key(private_key)
    return Account.from_key(normalized_key).address

# 计算私钥的 SHA-256 哈希值。
# 通常用于在不存储明文私钥的情况下，验证用户输入的私钥是否与之前记录的一致。
def private_key_hash(private_key: str) -> str:
    normalized_key = normalize_private_key(private_key)
    return hashlib.sha256(normalized_key.encode("utf-8")).hexdigest()


def private_key_to_public_key(private_key: str) -> str:
    normalized_key = normalize_private_key(private_key)
    value = int(normalized_key[2:], 16)
    private = ec.derive_private_key(value, ec.SECP256K1())
    public = private.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return "0x" + public.hex()


def build_fernet_from_private_key(private_key: str) -> Fernet:
    normalized_key = normalize_private_key(private_key)
    # 获取 SHA-256 的二进制摘要 (32 bytes)
    digest = hashlib.sha256(normalized_key.encode("utf-8")).digest()
    # 转换为 Fernet 需要的 base64 格式
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)

# 使用私钥加密文本内容。
# 返回 Base64 编码的密文字符串
def encrypt_text(content: str, private_key: str) -> str:
    fernet = build_fernet_from_private_key(private_key)
    return fernet.encrypt((content or "").encode("utf-8")).decode("utf-8")

# 使用私钥解密密文。
# 如果私钥错误或数据被篡改，抛出 ValueError。
def decrypt_text(cipher_text: str, private_key: str) -> str:
    fernet = build_fernet_from_private_key(private_key)
    try:
        return fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("私钥错误或数据已损坏，无法解密") from exc

# 加密二进制数据
def encrypt_binary(raw: bytes, private_key: str) -> bytes:
    fernet = build_fernet_from_private_key(private_key)
    return fernet.encrypt(raw or b"")

# 解密二进制数据
def decrypt_binary(cipher_bytes: bytes, private_key: str) -> bytes:
    fernet = build_fernet_from_private_key(private_key)
    try:
        return fernet.decrypt(cipher_bytes or b"")
    except InvalidToken as exc:
        raise ValueError("私钥错误或文件已损坏，无法解密") from exc


def generate_data_encryption_key() -> bytes:
    return os.urandom(32)


def _build_fernet_from_dek(dek: bytes) -> Fernet:
    if not isinstance(dek, (bytes, bytearray)) or len(dek) != 32:
        raise ValueError("DEK 必须是 32 字节")
    return Fernet(base64.urlsafe_b64encode(bytes(dek)))


def encrypt_text_with_dek(content: str, dek: bytes) -> str:
    fernet = _build_fernet_from_dek(dek)
    return fernet.encrypt((content or "").encode("utf-8")).decode("utf-8")


def decrypt_text_with_dek(cipher_text: str, dek: bytes) -> str:
    fernet = _build_fernet_from_dek(dek)
    try:
        return fernet.decrypt((cipher_text or "").encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("DEK 错误或数据已损坏，无法解密文本") from exc


def encrypt_binary_with_dek(raw: bytes, dek: bytes) -> bytes:
    fernet = _build_fernet_from_dek(dek)
    return fernet.encrypt(raw or b"")


def decrypt_binary_with_dek(cipher_bytes: bytes, dek: bytes) -> bytes:
    fernet = _build_fernet_from_dek(dek)
    try:
        return fernet.decrypt(cipher_bytes or b"")
    except InvalidToken as exc:
        raise ValueError("DEK 错误或数据已损坏，无法解密文件") from exc


def _load_public_key(public_key_hex: str):
    key = (public_key_hex or "").strip()
    if key.startswith("0x"):
        key = key[2:]
    raw = bytes.fromhex(key)
    return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), raw)


def _load_private_key(private_key: str):
    normalized = normalize_private_key(private_key)
    value = int(normalized[2:], 16)
    return ec.derive_private_key(value, ec.SECP256K1())


def _derive_wrap_key(shared_secret: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"health-data-dek-wrap-v1",
    ).derive(shared_secret)


def wrap_dek_for_public_key(dek: bytes, public_key_hex: str) -> str:
    if len(dek) != 32:
        raise ValueError("DEK 必须是 32 字节")
    recipient_public = _load_public_key(public_key_hex)
    ephemeral_private = ec.generate_private_key(ec.SECP256K1())
    shared_secret = ephemeral_private.exchange(ec.ECDH(), recipient_public)
    wrap_key = _derive_wrap_key(shared_secret)

    nonce = os.urandom(12)
    ciphertext = AESGCM(wrap_key).encrypt(nonce, dek, b"health-dek")
    ephemeral_public = ephemeral_private.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )

    payload = {
        "v": 1,
        "epk": base64.urlsafe_b64encode(ephemeral_public).decode("utf-8"),
        "n": base64.urlsafe_b64encode(nonce).decode("utf-8"),
        "ct": base64.urlsafe_b64encode(ciphertext).decode("utf-8"),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def unwrap_dek_with_private_key(wrapped_payload: str, private_key: str) -> bytes:
    if not wrapped_payload:
        raise ValueError("缺少被包装的 DEK")
    try:
        payload = json.loads(wrapped_payload)
        ephemeral_public = base64.urlsafe_b64decode(payload["epk"].encode("utf-8"))
        nonce = base64.urlsafe_b64decode(payload["n"].encode("utf-8"))
        ciphertext = base64.urlsafe_b64decode(payload["ct"].encode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ValueError("DEK 包装数据格式非法") from exc

    private = _load_private_key(private_key)
    peer_public = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), ephemeral_public)
    shared_secret = private.exchange(ec.ECDH(), peer_public)
    wrap_key = _derive_wrap_key(shared_secret)

    try:
        return AESGCM(wrap_key).decrypt(nonce, ciphertext, b"health-dek")
    except Exception as exc:  # noqa: BLE001
        raise ValueError("私钥错误或 DEK 包装已损坏") from exc


# 验证用户私钥是否正确。
# 检查私钥哈希是否匹配，并且推导出的地址与记录的地址一致。
def verify_user_private_key(private_key: str, wallet_address: str | None, saved_hash: str | None) -> bool:
    if not private_key or not wallet_address or not saved_hash:
        return False

    if private_key_hash(private_key) != saved_hash:
        return False

    return private_key_to_address(private_key).lower() == wallet_address.lower()
