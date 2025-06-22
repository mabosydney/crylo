# Anonymous Weekly Lottery

This repository contains a lightweight Monero lottery designed for a small VPS with only 25 GB of storage. Users buy tickets anonymously and a weekly draw selects the winning number.

## Folder Overview
- `backend/` – Flask application and SQLite database
- `frontend/` – Static website files
- `monero_setup/` – Helper script for wallet RPC
- `config.json` – Editable settings (wallet address, draw schedule, etc.)

## Setup on Ubuntu 22.04
Follow the steps below exactly in a terminal. No coding knowledge is required.

1. **Install packages**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip tmux wget git
   ```
2. **Get the code**
   ```bash
   git clone https://github.com/mabosydney/crylo.git
   cd crylo
   ```
3. **Create the Python environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install flask requests
   ```
4. **Download and extract Monero**
   ```bash
   wget https://downloads.getmonero.org/cli/monero-linux-x64-v0.18.3.1.tar.bz2
   tar -xjf monero-linux-x64-v0.18.3.1.tar.bz2
   sudo mv monero-x86_64-linux-gnu-v0.18.3.1 /opt/monero
   ```
5. **Create a wallet and start `monero-wallet-rpc`**
   Run these commands in a tmux session so they keep running after you close PuTTY:
   ```bash
   tmux new -s wallet
   /opt/monero/monero-wallet-cli --generate-new-wallet lottery --password advance
   /opt/monero/monero-wallet-rpc --wallet-file lottery --password advance \
       --rpc-bind-port 18083 --disable-rpc-login \
       --daemon-address 88.3.210.198:18081
   # detach from tmux with Ctrl+B then D
   ```
   The wallet RPC uses the remote node `88.3.210.198:18081` so the blockchain
   stays off your VPS and disk usage remains under 25 GB.
6. **Edit `config.json`**
   Set `owner_address` to your wallet address and adjust the ticket price or draw
   time if needed.  If you start `monero-wallet-rpc` on a different port,
   update `wallet_rpc_url` as well.
7. **Run the Flask server**
   ```bash
   tmux new -s flask
   source venv/bin/activate
   python3 -m backend.app
   # detach with Ctrl+B then D
   ```
   Visit `http://YOUR_SERVER_IP:5000` in your browser to access the site.
   When buying tickets, enter a valid Monero address (95 or 106 characters) so winnings can be sent to you.
8. **Run the weekly draw**
   ```bash
   source venv/bin/activate
   python3 -m backend.draw
   ```
   You can automate this with `cron` to run every week.

## Reconnecting
If you disconnect or reboot, reattach the sessions with:
```bash
tmux attach -t wallet
# or
tmux attach -t flask
```

## Game Rules
1. Each ticket costs **0.1 XMR** and is assigned a random six‑digit number.
2. Pay the same address shown after purchase for each ticket. Only confirmed payments count.
3. The prize pool equals all paid tickets before the draw. Winners split the pool after a 5% fee goes to the owner address.
4. Draws occur on the configured day and time (see `config.json`).

## License
MIT
