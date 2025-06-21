# Monero Setup Guide

These instructions explain how to install `monerod` and `monero-wallet-rpc` on Ubuntu.

1. **Install dependencies**
   ```bash
   sudo apt update && sudo apt install -y wget tor
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
   /opt/monero/monero-wallet-rpc --wallet-file lottery --rpc-bind-port 18083 --disable-rpc-login --daemon-host localhost
   ```
4. **Python wrapper example**
   See `wallet_rpc.py` in this folder for Python helper functions.
