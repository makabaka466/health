import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
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


# 验证用户私钥是否正确。
# 检查私钥哈希是否匹配，并且推导出的地址与记录的地址一致。
def verify_user_private_key(private_key: str, wallet_address: str | None, saved_hash: str | None) -> bool:
    if not private_key or not wallet_address or not saved_hash:
        return False

    if private_key_hash(private_key) != saved_hash:
        return False

    return private_key_to_address(private_key).lower() == wallet_address.lower()
