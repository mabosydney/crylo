# Anonymous Weekly Lottery
This project is designed for small servers (2GB RAM, 25GB disk).

This project provides a simple Monero-based lottery that can run on a small VPS. Users purchase tickets anonymously using Monero and a weekly draw determines the winners.

## Folder Structure

- `backend/` – Flask application and database
- `frontend/` – Static HTML/CSS pages
- `monero_setup/` – Instructions and helper for Monero wallet RPC
- `config.json` – Configuration values (ticket price, wallet address, etc.)

## Setup Guide (Ubuntu)

1. **Install system packages**
   ```bash
   sudo apt update && sudo apt install -y python3 python3-venv python3-pip
   ```
2. **Clone repository**
   ```bash
   git clone https://github.com/mabosydney/crylo.git
   cd crylo
   ```
3. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install flask requests
   ```
4. **Configure Monero wallet RPC** – see `monero_setup/README.md` to install `monerod` and `monero-wallet-rpc`. Start `monero-wallet-rpc` so the Flask app can talk to it.
5. **Run the Flask backend**
   ```bash
   python3 -m backend.app
   ```
   The site is now available on `http://your-server-ip:5000`.
6. **Running the draw**
   ```bash
   python3 -m backend.draw
   ```
   Add this command to a weekly cron job to automate draws.

### Resuming after closing PuTTY
Use the `screen` or `tmux` command before running the server so that it stays active when you disconnect.


### Wallet RPC and Low Disk Usage
Running a Monero node requires significant disk space. To keep the server under
25GB you can connect `monero-wallet-rpc` to a **remote node** instead of running
`monerod` locally:

```bash
/opt/monero/monero-wallet-rpc --wallet-file lottery --rpc-bind-port 18083 \
  --disable-rpc-login --daemon-address node.moneroworld.com:18089
```
Using a remote node avoids storing the blockchain locally. See
`monero_setup/README.md` for installation details.

## Game Rules
1. Choose six numbers from 1–49.
2. Pay `0.01 XMR` to the provided address.
3. Once payment is confirmed your ticket enters the next draw.
4. Random numbers are drawn weekly. Winners share the pot minus a 5% fee sent to the owner wallet defined in `config.json`.

## License
MIT
