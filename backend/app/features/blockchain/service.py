import hashlib
import json
from typing import Any, Optional

from web3 import Web3

from app.config import settings


class HealthDataChainService:
    def __init__(self) -> None:
        self.web3 = Web3(Web3.HTTPProvider(settings.WEB3_PROVIDER_URI))
        self._enabled = bool(settings.HEALTH_DATA_CONTRACT_ADDRESS and settings.HEALTH_DATA_CONTRACT_ABI_JSON)
        self._contract = None

        if self._enabled:
            abi = json.loads(settings.HEALTH_DATA_CONTRACT_ABI_JSON)
            checksum_address = Web3.to_checksum_address(settings.HEALTH_DATA_CONTRACT_ADDRESS)
            self._contract = self.web3.eth.contract(address=checksum_address, abi=abi)

    @property
    def enabled(self) -> bool:
        return self._enabled and self._contract is not None

    def to_bytes32(self, value: str) -> bytes:
        hex_value = value[2:] if value.startswith("0x") else value
        raw = bytes.fromhex(hex_value)
        if len(raw) != 32:
            raise ValueError("bytes32 ??????? 32 ??")
        return raw

    def digest_to_bytes32(self, value: str) -> bytes:
        return hashlib.sha256(value.encode("utf-8")).digest()

    def _build_tx_options(self, from_address: str, nonce: int) -> dict[str, Any]:
        return {
            "from": from_address,
            "nonce": nonce,
            "gas": 400000,
            "gasPrice": self.web3.to_wei("2", "gwei"),
            "chainId": self.web3.eth.chain_id,
        }

    def _send_transaction(self, function_call: Any, owner_private_key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        account = self.web3.eth.account.from_key(owner_private_key)
        nonce = self.web3.eth.get_transaction_count(account.address)
        tx = function_call.build_transaction(self._build_tx_options(account.address, nonce))
        signed = self.web3.eth.account.sign_transaction(tx, private_key=owner_private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
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
        if not self.enabled:
            return None

        function_call = self._contract.functions.storeHealthData(
            self.to_bytes32(data_hash_hex),
            self.digest_to_bytes32(encrypted_digest_source),
            data_type,
        )
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
        if not self.enabled:
            return None

        function_call = self._contract.functions.updateHealthData(
            self.to_bytes32(data_id_hex),
            self.to_bytes32(data_hash_hex),
            self.digest_to_bytes32(encrypted_digest_source),
        )
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


chain_service = HealthDataChainService()
