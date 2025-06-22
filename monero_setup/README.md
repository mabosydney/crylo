# Monero Setup Guide

These instructions explain how to install `monero-wallet-rpc` on Ubuntu and connect it to a remote node so no blockchain is stored locally.

1. **Install dependencies**
   ```bash
   sudo apt update && sudo apt install -y wget
   ```
2. **Download binaries**
   ```bash
   wget https://downloads.getmonero.org/cli/monero-linux-x64-v0.18.3.1.tar.bz2
   tar -xjf monero-linux-x64-v0.18.3.1.tar.bz2
   sudo mv monero-x86_64-linux-gnu-v0.18.3.1 /opt/monero
   ```
3. **Create wallet and start RPC**
   ```bash
   /opt/monero/monero-wallet-cli --generate-new-wallet lottery --password advance
   /opt/monero/monero-wallet-rpc --wallet-file lottery --password advance \
     --rpc-bind-port 18083 --disable-rpc-login --trusted-daemon \
     --daemon-address 88.3.210.198:18081
   ```
   Verify it responds:
   ```bash
   curl -d '{"jsonrpc":"2.0","id":0,"method":"get_balance"}' \
        http://localhost:18083/json_rpcn
   ```
   `monerod` is not started here. The wallet RPC connects to the remote node
   `88.3.210.198:18081` so the blockchain is stored remotely and disk usage
   stays under 25 GB.
4. **Python wrapper example**
   See `wallet_rpc.py` in this folder for Python helper functions.
