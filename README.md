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
   sudo apt update
   sudo apt install -y python3 python3-venv python3-pip tmux wget

2. **Download the project**

3. **Create the Python environment**

4. **Download the Monero CLI tools**
   ```bash
   wget https://downloads.getmonero.org/cli/monero-linux-x64-v0.18.3.1.tar.bz2
   tar -xjf monero-linux-x64-v0.18.3.1.tar.bz2
   sudo mv monero-x86_64-linux-gnu-v0.18.3.1 /opt/monero
   ```

5. **Create a wallet and start wallet RPC**
   Run these commands inside `tmux` so they keep running when you close PuTTY:
   /opt/monero/monero-wallet-cli --generate-new-wallet lottery --password advance
   /opt/monero/monero-wallet-rpc --wallet-file lottery --password advance \
       --rpc-bind-port 18083 --disable-rpc-login \
       --daemon-address node.moneroworld.com:18089
   # detach with Ctrl+B then D
   The wallet RPC connects to `node.moneroworld.com` so the blockchain stays remote and disk use stays below 25 GB.

6. **Edit `config.json`**
   Set `owner_address` to your main wallet address and adjust any other values you wish.

7. **Start the Flask web app**
   Use a second tmux session for the web server:
   # detach with Ctrl+B then D
   ```
   Visit `http://<your-server-ip>:5000` in a browser.

8. **Running the weekly draw**
   To trigger a draw manually:
   Add this command to `cron` if you want the draw to run automatically every week.
## After Reboot or Disconnect
To resume, attach back to your tmux sessions:
tmux attach -t wallet
# or
tmux attach -t flask
1. Pick six numbers between 1 and 49.
2. Pay 0.01 XMR to the subaddress shown after buying a ticket.
3. When the draw is run, winning tickets split the pot minus a 5 % fee sent to `owner_address`.
6. **Start the Flask app** in another tmux session
   ```bash
   tmux new -s flask
   source venv/bin/activate
   python3 -m backend.app
   ```
   The site will be available on `http://your-server-ip:5000`.
7. **Run the weekly draw**
   ```bash
   python3 -m backend.draw
   ```
   Schedule this command with `cron` to automate weekly draws.


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
