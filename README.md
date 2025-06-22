# Anonymous Weekly Lottery

This project is a simple Monero lottery that runs on a tiny VPS (2 GB RAM and only 25 GB of disk). Users buy tickets anonymously with Monero and a weekly draw pays out the prize.

## Folder Structure
- `backend/` – Flask app and SQLite database
- `frontend/` – Static HTML/CSS for the website
- `monero_setup/` – Helper script for the Monero wallet RPC
- `config.json` – Settings such as your wallet address and ticket price

## Setup on Ubuntu 22.04
Follow these steps exactly in a terminal. Each command is shown in full.

1. **Install system packages**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip tmux wget
   ```

2. **Download the project**
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

4. **Download the Monero CLI tools**
   ```bash
   wget https://downloads.getmonero.org/cli/monero-linux-x64-v0.18.3.1.tar.bz2
   tar -xjf monero-linux-x64-v0.18.3.1.tar.bz2
   sudo mv monero-x86_64-linux-gnu-v0.18.3.1 /opt/monero
   ```

5. **Create a wallet and start wallet RPC**
   Run these commands inside `tmux` so they keep running when you close PuTTY:
   ```bash
   tmux new -s wallet
   /opt/monero/monero-wallet-cli --generate-new-wallet lottery --password advance
   /opt/monero/monero-wallet-rpc --wallet-file lottery --password advance \
       --rpc-bind-port 18083 --disable-rpc-login \
       --daemon-address node.moneroworld.com:18089
   # detach with Ctrl+B then D
   ```
   The wallet RPC connects to `node.moneroworld.com` so the blockchain stays remote and disk use stays below 25 GB.

6. **Edit `config.json`**
   Set `owner_address` to your main wallet address and adjust any other values you wish.

7. **Start the Flask web app**
   Use a second tmux session for the web server:
   ```bash
   tmux new -s flask
   source venv/bin/activate
   python3 -m backend.app
   # detach with Ctrl+B then D
   ```
   Visit `http://<your-server-ip>:5000` in a browser.

8. **Running the weekly draw**
   To trigger a draw manually:
   ```bash
   python3 -m backend.draw
   ```
   Add this command to `cron` if you want the draw to run automatically every week.

## After Reboot or Disconnect
To resume, attach back to your tmux sessions:
```bash
tmux attach -t wallet
# or
tmux attach -t flask
```

## Game Rules
1. Choose how many tickets you want and the server will create an address for each ticket.
2. Send **0.1 XMR per ticket** to the provided addresses.
3. Each ticket receives a random six-digit number.
4. When the draw runs every week, a winning number is generated.
5. All tickets matching that number split the pot after a 5% fee is sent to `owner_address`.

## License
MIT
