"""Example helper for monero-wallet-rpc"""
import requests

class WalletRPC:
    def __init__(self, url="http://localhost:18083/json_rpc"):
        self.url = url
        self.id_counter = 0

    def _call(self, method, params=None):
        self.id_counter += 1
        payload = {"jsonrpc": "2.0", "id": self.id_counter, "method": method, "params": params or {}}
        r = requests.post(self.url, json=payload)
        r.raise_for_status()
        return r.json()["result"]

    def create_address(self, account_index=0):
        return self._call("create_address", {"account_index": account_index})

    def get_transfers(self, **kwargs):
        return self._call("get_transfers", kwargs)

    def transfer(self, address, amount):
        destinations = [{"address": address, "amount": int(amount * 1e12)}]
        return self._call("transfer", {"destinations": destinations})
