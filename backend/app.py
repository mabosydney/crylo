from flask import Flask, request, redirect, url_for, render_template, abort
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from .monero_rpc import MoneroRPC
from .config import load_config
from .db import init_db, get_conn

config = load_config()
app = Flask(__name__)

RPC_URL = 'http://localhost:18083/json_rpc'
monero = MoneroRPC(RPC_URL)

init_db()

def generate_numbers():
    """Return six random numbers between 1 and 49."""
    return [int.from_bytes(os.urandom(2), 'big') % 49 + 1 for _ in range(6)]

@app.route('/')
def index():
    """Front page with ticket purchase form."""
    return render_template('index.html', price=config['ticket_price'])

@app.route('/buy', methods=['POST'])
def buy():
    """Create a new ticket and display the subaddress for payment."""
    numbers = request.form.getlist('numbers')
    if len(numbers) != 6:
        abort(400, 'Choose exactly 6 numbers')
    nums = ','.join(sorted(numbers))
    addr_res = monero.create_subaddress()
    subaddress = addr_res['address']
    sub_index = addr_res['address_index']
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO tickets (numbers, subaddress_index, subaddress) VALUES (?, ?, ?)',
              (nums, sub_index, subaddress))
    ticket_id = c.lastrowid
    conn.commit()
    conn.close()
    return render_template('ticket.html', subaddress=subaddress, ticket_id=ticket_id, price=config['ticket_price'])

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
    row = c.execute('SELECT week, numbers, winners, payout FROM results ORDER BY week DESC LIMIT 1').fetchone()
    conn.close()
    return render_template('results.html', result=row)

@app.route('/draw', methods=['POST'])
def draw():
    """Perform the weekly draw and send payouts."""
    if request.form.get('password') != config['admin_password']:
        abort(403)
    numbers = generate_numbers()
    conn = get_conn()
    c = conn.cursor()
    week = int(datetime.utcnow().strftime('%Y%W'))
    entries = c.execute('SELECT id, numbers, subaddress FROM tickets WHERE paid=1 AND draw_week IS NULL').fetchall()
    winners = []
    for eid, nums, addr in entries:
        nums_set = set(map(int, nums.split(',')))
        if nums_set == set(numbers):
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
    c.execute('INSERT OR REPLACE INTO results (week, numbers, winners, payout) VALUES (?,?,?,?)', (week, ','.join(map(str,numbers)), ','.join(a for _,a in winners), payout))
    conn.commit()
    conn.close()
    return 'Draw complete'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config['port'])
