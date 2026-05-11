import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

from web3 import Web3

from app.config import settings


class HealthDataChainService:
    def __init__(self) -> None:
        self.web3 = Web3(
            Web3.HTTPProvider(
                settings.WEB3_PROVIDER_URI,
                request_kwargs={"timeout": settings.WEB3_RPC_TIMEOUT_SECONDS},
            )
        )
        self._configured = bool(settings.HEALTH_DATA_CONTRACT_ADDRESS and settings.HEALTH_DATA_CONTRACT_ABI_JSON)
        self._contract = None
        self._contract_abi = None
        self._contract_address = None

        if self._configured:
            try:
                self._contract_abi = json.loads(settings.HEALTH_DATA_CONTRACT_ABI_JSON)
                self._contract_address = Web3.to_checksum_address(settings.HEALTH_DATA_CONTRACT_ADDRESS)
            except Exception:
                self._configured = False

        self._ensure_contract_bound()

    @property
    def enabled(self) -> bool:
        self._ensure_contract_bound()
        return self._configured and self._contract is not None and self.rpc_connected

    @property
    def rpc_connected(self) -> bool:
        try:
            return self.web3.is_connected()
        except Exception:
            return False

    def _ensure_contract_bound(self) -> None:
        if not self._configured:
            return
        if not self.rpc_connected:
            self._contract = None
            return
        if self._contract is not None:
            return
        try:
            deployed_code = self.web3.eth.get_code(self._contract_address)
            if deployed_code and deployed_code != b"\x00":
                self._contract = self.web3.eth.contract(address=self._contract_address, abi=self._contract_abi)
        except Exception:
            self._contract = None

    def _gas_price_wei(self) -> int:
        return self.web3.to_wei(settings.WEB3_GAS_PRICE_GWEI, "gwei")

    def _parse_eth_amount(self, amount_eth: str | int | float | Decimal | None) -> Decimal:
        raw_value = settings.WEB3_AUTO_FUND_AMOUNT_ETH if amount_eth is None else amount_eth
        try:
            amount = Decimal(str(raw_value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Invalid ETH amount configured for faucet") from exc

        if amount <= 0:
            raise ValueError("Faucet amount must be greater than zero")
        return amount

    def to_bytes32(self, value: str) -> bytes:
        hex_value = value[2:] if value.startswith("0x") else value
        raw = bytes.fromhex(hex_value)
        if len(raw) != 32:
            raise ValueError("bytes32 value must be exactly 32 bytes")
        return raw

    def digest_to_bytes32(self, value: str) -> bytes:
        return hashlib.sha256(value.encode("utf-8")).digest()

    def _build_tx_options(self, from_address: str, nonce: int) -> dict[str, Any]:
        return {
            "from": from_address,
            "nonce": nonce,
            "gas": 400000,
            "gasPrice": self._gas_price_wei(),
            "chainId": self.web3.eth.chain_id,
        }

    def _send_transaction(self, function_call: Any, owner_private_key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        account = self.web3.eth.account.from_key(owner_private_key)
        nonce = self.web3.eth.get_transaction_count(account.address)
        tx = function_call.build_transaction(self._build_tx_options(account.address, nonce))
        signed = self.web3.eth.account.sign_transaction(tx, private_key=owner_private_key)
        raw_transaction = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction", None)
        if raw_transaction is None:
            raise AttributeError("SignedTransaction missing raw transaction bytes")
        tx_hash = self.web3.eth.send_raw_transaction(raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        return {
            "tx_hash": receipt.transactionHash.hex(),
            "status": receipt.status,
            "receipt": receipt,
            "owner": account.address,
        }

    def _extract_data_stored_event(self, receipt: Any) -> Optional[str]:
        if not self.enabled:
            return None
        try:
            events = self._contract.events.DataStored().process_receipt(receipt)
            if not events:
                return None
            data_id = events[0]["args"].get("dataId")
            return Web3.to_hex(data_id) if data_id is not None else None
        except Exception:
            return None

    def store_health_data(
        self,
        *,
        owner_private_key: str,
        data_hash_hex: str,
        encrypted_digest_source: str,
        data_type: str,
    ) -> dict[str, Any] | None:
        """新增健康数据存证：调用合约 storeHealthData 并返回交易结果。"""
        if not self.enabled:
            return None

        # 组装合约调用参数：业务哈希、密文摘要哈希、数据类型。
        function_call = self._contract.functions.storeHealthData(
            self.to_bytes32(data_hash_hex),
            self.digest_to_bytes32(encrypted_digest_source),
            data_type,
        )
        # 发送链上交易并尝试从事件中解析 data_id。
        result = self._send_transaction(function_call, owner_private_key)
        if not result:
            return None
        result["data_id"] = self._extract_data_stored_event(result.get("receipt"))
        result.pop("receipt", None)
        return result

    def update_health_data(
        self,
        *,
        owner_private_key: str,
        data_id_hex: str,
        data_hash_hex: str,
        encrypted_digest_source: str,
    ) -> dict[str, Any] | None:
        """更新已有存证：调用合约 updateHealthData 并返回交易结果。"""
        if not self.enabled:
            return None

        # 使用已存在的 data_id 更新链上哈希与密文摘要哈希。
        function_call = self._contract.functions.updateHealthData(
            self.to_bytes32(data_id_hex),
            self.to_bytes32(data_hash_hex),
            self.digest_to_bytes32(encrypted_digest_source),
        )
        # 提交更新交易，成功后沿用原 data_id 返回。
        result = self._send_transaction(function_call, owner_private_key)
        if not result:
            return None
        result["data_id"] = data_id_hex
        result.pop("receipt", None)
        return result

    def get_health_record(self, *, data_id_hex: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        raw = self._contract.functions.healthRecords(self.to_bytes32(data_id_hex)).call()
        owner = raw[3]
        is_active = bool(raw[4])
        if not owner or owner == "0x0000000000000000000000000000000000000000" or not is_active:
            return None

        return {
            "data_hash": Web3.to_hex(raw[0]),
            "encrypted_digest": Web3.to_hex(raw[1]),
            "timestamp": raw[2],
            "owner": owner,
            "is_active": is_active,
            "data_type": raw[5],
            "status": raw[6],
        }

    def get_balance_eth(self, address: str) -> str:
        checksum_address = Web3.to_checksum_address(address)
        balance_wei = self.web3.eth.get_balance(checksum_address)
        return str(self.web3.from_wei(balance_wei, "ether"))

    def grant_test_eth(
        self,
        to_address: str,
        *,
        amount_eth: str | int | float | Decimal | None = None,
    ) -> dict[str, Any] | None:
        if not self.rpc_connected:
            return None

        amount = self._parse_eth_amount(amount_eth)
        checksum_to_address = Web3.to_checksum_address(to_address)
        available_accounts = self.web3.eth.accounts
        if not available_accounts:
            raise ValueError("No unlocked Ganache account is available for faucet funding")

        from_address = settings.WEB3_FAUCET_FROM_ADDRESS or available_accounts[0]
        checksum_from_address = Web3.to_checksum_address(from_address)
        if checksum_from_address not in {Web3.to_checksum_address(item) for item in available_accounts}:
            raise ValueError("Configured faucet account is not unlocked on the current Ganache node")

        value_wei = self.web3.to_wei(amount, "ether")
        tx_hash = self.web3.eth.send_transaction(
            {
                "from": checksum_from_address,
                "to": checksum_to_address,
                "value": value_wei,
                "gas": 21000,
                "gasPrice": self._gas_price_wei(),
                "chainId": self.web3.eth.chain_id,
            }
        )
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        return {
            "tx_hash": receipt.transactionHash.hex(),
            "status": receipt.status,
            "from": checksum_from_address,
            "to": checksum_to_address,
            "amount_eth": str(amount),
            "wallet_balance_eth": self.get_balance_eth(checksum_to_address),
        }


chain_service = HealthDataChainService()
