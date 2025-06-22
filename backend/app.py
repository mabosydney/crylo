from flask import Flask, request, render_template, abort
import os
from datetime import datetime, timedelta
import calendar
from .monero_rpc import MoneroRPC
from .config import load_config
from .db import init_db, get_conn

config = load_config()
app = Flask(__name__)

RPC_URL = 'http://localhost:18083/json_rpc'
monero = MoneroRPC(RPC_URL)

init_db()

def generate_ticket_number() -> str:
    """Return a random six-digit ticket number as a string."""
    return f"{int.from_bytes(os.urandom(3), 'big') % 1000000:06d}"

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
    """Create ticket(s) and show subaddresses for payment."""
    try:
        qty = int(request.form.get('quantity', '1'))
    except ValueError:
        abort(400, 'Invalid quantity')
    if qty <= 0:
        abort(400, 'Quantity must be positive')

    tickets = []
    conn = get_conn()
    c = conn.cursor()
    for _ in range(qty):
        addr_res = monero.create_subaddress()
        subaddress = addr_res['address']
        sub_index = addr_res['address_index']
        number = generate_ticket_number()
        c.execute(
            'INSERT INTO tickets (ticket_number, subaddress_index, subaddress) VALUES (?,?,?)',
            (number, sub_index, subaddress),
        )
        ticket_id = c.lastrowid
        tickets.append({'id': ticket_id, 'number': number, 'address': subaddress})
    conn.commit()
    conn.close()

    total = qty * config['ticket_price']
    return render_template('ticket.html', tickets=tickets, price=config['ticket_price'], total=total)

@app.route('/status/<int:ticket_id>')
def status(ticket_id):
    """Check whether payment for a ticket has been received."""
    conn = get_conn()
    c = conn.cursor()
    row = c.execute('SELECT paid, subaddress_index FROM tickets WHERE id=?', (ticket_id,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    paid, sub_index = row
    if not paid:
        transfers = monero.get_transfers(**{
            'in': True,
            'account_index': 0,
            'subaddr_indices': [sub_index]
        })
        paid = False
        if 'in' in transfers:
            amount = sum(t['amount'] for t in transfers['in']) / 1e12
            if amount >= config['ticket_price']:
                conn = get_conn()
                c = conn.cursor()
                c.execute('UPDATE tickets SET paid=1 WHERE id=?', (ticket_id,))
                conn.commit()
                conn.close()
                paid = True
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
    week = int(datetime.utcnow().strftime('%Y%W'))
    entries = c.execute('SELECT id, ticket_number, subaddress FROM tickets WHERE paid=1 AND draw_week IS NULL').fetchall()
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
        for eid, addr in winners:
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
