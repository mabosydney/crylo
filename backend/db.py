import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / 'lottery.db'


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT NOT NULL,
            subaddress_index INTEGER,
            subaddress TEXT NOT NULL,
            paid INTEGER DEFAULT 0,
            draw_week INTEGER
        )'''
    )
    c.execute(
        '''CREATE TABLE IF NOT EXISTS results (
            week INTEGER PRIMARY KEY,
            winning_number TEXT NOT NULL,
            winners TEXT,
            payout REAL
        )'''
    
    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(DB_PATH)
