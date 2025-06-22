import requests
import json
from typing import Optional

class MoneroRPC:
    """Simple wrapper around monero-wallet-rpc JSON RPC"""

    def __init__(self, url: str, username: Optional[str] = None, password: Optional[str] = None):
        self.url = url
        self.auth = (username, password) if username and password else None
        self.id_counter = 0

    def _call(self, method: str, params: dict):
        self.id_counter += 1
        payload = {
            "jsonrpc": "2.0",
            "id": self.id_counter,
            "method": method,
            "params": params,
        }
        try:
            response = requests.post(self.url, json=payload, auth=self.auth, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionError(f"Wallet RPC unreachable at {self.url}: {e}")
        res = response.json()
        if 'error' in res:
            raise RuntimeError(res['error'])
        return res['result']

    def create_subaddress(self, account_index: int = 0):
        return self._call("create_address", {"account_index": account_index})

    def get_balance(self, account_index: int = 0, address_indices=None):
        params = {"account_index": account_index}
        if address_indices is not None:
            params["address_indices"] = address_indices
        return self._call("get_balance", params)

    def get_transfers(self, **kwargs):
        return self._call("get_transfers", kwargs)

    def transfer(self, destinations, **kwargs):
        params = {"destinations": destinations}
        params.update(kwargs)
        return self._call("transfer", params)
