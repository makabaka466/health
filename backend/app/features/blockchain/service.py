import hashlib
import json
from typing import Any

from web3 import Web3

from app.config import settings


class HealthDataChainService:
    def __init__(self) -> None:
        self.web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
        # 检查配置是否完整，决定服务是否可用
        self._enabled = bool(settings.HEALTH_DATA_CONTRACT_ADDRESS and settings.HEALTH_DATA_CONTRACT_ABI_JSON)
        self._contract = None

        if self._enabled:
            # 解析 ABI (Application Binary Interface)，这是与合约交互的说明书
            abi = json.loads(settings.HEALTH_DATA_CONTRACT_ABI_JSON)
            # 将合约地址转换为校验和格式，确保地址格式正确
            checksum_address = Web3.to_checksum_address(settings.HEALTH_DATA_CONTRACT_ADDRESS)
            # 创建合约对象，用于与智能合约交互
            self._contract = self.web3.eth.contract(address=checksum_address, abi=abi)

    @property
    def enabled(self) -> bool:
        # 公开属性，用于外部判断服务是否就绪。
        # 必须同时满足：配置已加载 AND 合约对象已实例化。
        return self._enabled and self._contract is not None

    # 将十六进制字符串转换为固定的 32 字节 (bytes32)
    def to_bytes32(self, value: str) -> bytes:
        hex_value = value[2:] if value.startswith("0x") else value
        raw = bytes.fromhex(hex_value)
        if len(raw) != 32:
            raise ValueError("bytes32 参数长度必须为 32 字节")
        return raw

    def digest_to_bytes32(self, value: str) -> bytes:
        digest = hashlib.sha256(value.encode("utf-8")).digest()
        return digest

    def store_health_data(
        self,
        *,
        owner_private_key: str,       # 私钥作为参数传入
        data_hash_hex: str,           # 健康数据内容的哈希 (例如文件哈希)
        encrypted_digest_source: str, # 加密数据源的摘要 (字符串)
        data_type: str,               # 数据类型标识
    ) -> dict[str, Any] | None:
        # 将健康数据的元数据存证到区块链
        # 守卫检查：如果服务未配置，直接放弃
        if not self.enabled:
            return None

        # 恢复账户对象
        # 从私钥推导出公钥和地址
        account = self.web3.eth.account.from_key(owner_private_key)
        nonce = self.web3.eth.get_transaction_count(account.address)

        # 构建交易
        # 调用智能合约的 storeHealthData 函数
        tx = self._contract.functions.storeHealthData(
            self.to_bytes32(data_hash_hex),          # 参数 1: bytes32
            self.digest_to_bytes32(encrypted_digest_source), # 参数 2: bytes32 (自动哈希)
            data_type,                               # 参数 3: string
        ).build_transaction(
            {
                "from": account.address,             # 发送者地址
                "nonce": nonce,                      # 当前 nonce
                "gas": 400000,                       # 预估 Gas 上限 (硬编码，可能存在 Gas 不足风险)
                "gasPrice": self.web3.to_wei("2", "gwei"), # Gas 价格 (硬编码，网络拥堵时可能失败)
                "chainId": self.web3.eth.chain_id,   # 链 ID，防止跨链重放
            }
        )
        # 签名交易
        # 使用私钥对交易数据进行椭圆曲线签名
        signed = self.web3.eth.account.sign_transaction(tx, private_key=owner_private_key)
        
        # 发送交易
        # 将签名后的交易广播到以太坊网络
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        
        # 等待交易确认
        # 轮询等待交易被打包进区块
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "tx_hash": receipt.transactionHash.hex(),# 交易哈希
            "status": receipt.status,                # 1 表示成功，0 表示失败
        }


chain_service = HealthDataChainService()
