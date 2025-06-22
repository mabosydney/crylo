from flask import Flask, request, render_template, abort
import os
from datetime import datetime, timedelta
import calendar
import re
from .monero_rpc import MoneroRPC
from .config import load_config
from .db import init_db, get_conn

config = load_config()
app = Flask(__name__)

# connect to monero-wallet-rpc using the URL from config
RPC_URL = config.get('wallet_rpc_url', 'http://localhost:18083/json_rpc')
monero = MoneroRPC(RPC_URL)

init_db()

def generate_ticket_number() -> str:
    """Return a random six-digit ticket number as a string."""
    return f"{int.from_bytes(os.urandom(3), 'big') % 1000000:06d}"

ADDRESS_RE = re.compile(r"^[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93,105}$")


def validate_address(addr: str) -> bool:
    """Return True if ``addr`` looks like a valid Monero address."""
    return bool(ADDRESS_RE.fullmatch(addr))

def sync_payments() -> None:
    """Mark unpaid tickets as paid based on total confirmed balance."""
    transfers = monero.get_transfers(**{"in": True})
    total_received = 0.0
    if 'in' in transfers:
        total_received = sum(t['amount'] for t in transfers['in']) / 1e12
    conn = get_conn()
    c = conn.cursor()
    paid_count = c.execute('SELECT COUNT(*) FROM tickets WHERE paid=1').fetchone()[0]
    should_be_paid = int(total_received / config['ticket_price'])
    diff = should_be_paid - paid_count
    if diff > 0:
        ids = c.execute('SELECT id FROM tickets WHERE paid=0 ORDER BY id LIMIT ?', (diff,)).fetchall()
        for row in ids:
            c.execute('UPDATE tickets SET paid=1 WHERE id=?', (row[0],))
    conn.commit()
    conn.close()

def _next_draw_datetime() -> datetime:
    """Calculate the datetime of the next scheduled draw in UTC."""
    now = datetime.utcnow()
    weekday = list(calendar.day_name).index(config['draw_day'])
    draw_time = datetime.strptime(config['draw_time'], '%H:%M').time()
    days_ahead = (weekday - now.weekday()) % 7
    draw_date = now.date() + timedelta(days=days_ahead)
    draw_dt = datetime.combine(draw_date, draw_time)
    if draw_dt <= now:
        draw_dt += timedelta(days=7)
    return draw_dt

@app.route('/')
def index():
    """Front page with ticket purchase form and draw info."""
    sync_payments()
    conn = get_conn()
    c = conn.cursor()
    count = c.execute(
        'SELECT COUNT(*) FROM tickets WHERE paid=1 AND draw_week IS NULL'
    ).fetchone()[0]
    conn.close()
    pot_total = count * config['ticket_price']

    next_dt = _next_draw_datetime()
    delta = next_dt - datetime.utcnow()
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes = rem // 60
    countdown = f"{days}d {hours}h {minutes}m"

    return render_template(
        'index.html',
        price=config['ticket_price'],
        pot_total=pot_total,
        countdown=countdown,
    )

@app.route('/buy', methods=['POST'])
def buy():
    """Create ticket(s) and show payment instructions."""
    try:
        qty = int(request.form.get('quantity', '1'))
    except ValueError:
        abort(400, 'Invalid quantity')
    if qty <= 0:
        abort(400, 'Quantity must be positive')
    addr = request.form.get('address', '').strip()
    if not addr:
        abort(400, 'Wallet address required')
    if not validate_address(addr):
        abort(400, 'Invalid wallet address')
    tickets = []
    conn = get_conn()
    c = conn.cursor()
    for _ in range(qty):
        number = generate_ticket_number()
        c.execute(
            'INSERT INTO tickets (ticket_number, user_address) VALUES (?,?)',
            (number, addr),
        )
        ticket_id = c.lastrowid
        tickets.append({'id': ticket_id, 'number': number})
    conn.commit()
    conn.close()

    total = qty * config['ticket_price']
    return render_template('ticket.html', tickets=tickets, price=config['ticket_price'], total=total, owner_address=config['owner_address'])

@app.route('/status/<int:ticket_id>')
def status(ticket_id):
    """Check whether payment for a ticket has been received."""
    sync_payments()
    conn = get_conn()
    c = conn.cursor()
    row = c.execute('SELECT paid FROM tickets WHERE id=?', (ticket_id,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    paid = bool(row[0])
    return render_template('status.html', paid=paid)

# Placeholder results
@app.route('/results')
def results():
    """Show the latest draw results."""
    conn = get_conn()
    c = conn.cursor()
    row = c.execute('SELECT week, winning_number, winners, payout FROM results ORDER BY week DESC LIMIT 1').fetchone()
    conn.close()
    return render_template('results.html', result=row)

@app.route('/draw', methods=['POST'])
def draw():
    """Perform the weekly draw and send payouts."""
    if request.form.get('password') != config['admin_password']:
        abort(403)
    winning = generate_ticket_number()
    conn = get_conn()
    c = conn.cursor()
    sync_payments()
    week = int(datetime.utcnow().strftime('%Y%W'))
    entries = c.execute('SELECT id, ticket_number, user_address FROM tickets WHERE paid=1 AND draw_week IS NULL').fetchall()
    winners = []
    for eid, num, addr in entries:
        if num == winning:
            winners.append((eid, addr))
        c.execute('UPDATE tickets SET draw_week=? WHERE id=?', (week, eid))
    payout = 0
    if winners:
        total_pool = len(entries) * config['ticket_price']
        fee_amt = total_pool * config['fee_percent'] / 100
        payout = (total_pool - fee_amt) / len(winners)
        if fee_amt > 0:
            monero.transfer([{"address": config['owner_address'], "amount": int(fee_amt*1e12)}])
        for _, addr in winners:
            monero.transfer([{"address": addr, "amount": int(payout*1e12)}])
    c.execute(
        'INSERT OR REPLACE INTO results (week, winning_number, winners, payout) VALUES (?,?,?,?)',
        (week, winning, ','.join(a for _, a in winners), payout),
    )
    conn.commit()
    conn.close()
    return 'Draw complete'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['port'])
