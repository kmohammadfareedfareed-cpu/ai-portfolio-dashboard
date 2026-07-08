"""
db.py
Lightweight SQLite persistence for saved watchlists, forecast run history,
and AI chat logs -- so state survives across Streamlit reruns and sessions.
"""
import sqlite3
import json
import os
from datetime import datetime

from config import DB_PATH


def _connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = _connect()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS watchlist (
        ticker TEXT PRIMARY KEY,
        added_at TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS forecast_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        order_used TEXT,
        metrics TEXT,
        created_at TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS chat_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT,
        question TEXT,
        answer TEXT,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()


def add_to_watchlist(ticker: str):
    conn = _connect()
    conn.execute(
        "INSERT OR IGNORE INTO watchlist (ticker, added_at) VALUES (?, ?)",
        (ticker.upper(), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def remove_from_watchlist(ticker: str):
    conn = _connect()
    conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
    conn.commit()
    conn.close()


def get_watchlist() -> list[str]:
    conn = _connect()
    rows = conn.execute("SELECT ticker FROM watchlist ORDER BY added_at").fetchall()
    conn.close()
    return [r[0] for r in rows]


def log_forecast_run(ticker: str, order, metrics: dict):
    conn = _connect()
    conn.execute(
        "INSERT INTO forecast_runs (ticker, order_used, metrics, created_at) VALUES (?, ?, ?, ?)",
        (ticker, str(order), json.dumps(metrics), datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def log_chat(ticker: str, question: str, answer: str):
    conn = _connect()
    conn.execute(
        "INSERT INTO chat_log (ticker, question, answer, created_at) VALUES (?, ?, ?, ?)",
        (ticker, question, answer, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_chat_history(ticker: str, limit: int = 20):
    conn = _connect()
    rows = conn.execute(
        "SELECT question, answer, created_at FROM chat_log WHERE ticker = ? ORDER BY id DESC LIMIT ?",
        (ticker, limit),
    ).fetchall()
    conn.close()
    return list(reversed(rows))
