"""Tiny SQLite persistence layer for de-duplication."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("trivaia.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            link TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            source TEXT NOT NULL,
            published TEXT,
            first_seen TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return conn


def init_db():
    with _connect() as conn:
        pass


def get_recent_links():
    with _connect() as conn:
        rows = conn.execute("SELECT link FROM articles").fetchall()
    return {row[0] for row in rows}


def save_articles(articles):
    with _connect() as conn:
        conn.executemany(
            """INSERT OR IGNORE INTO articles(link, title, source, published)
               VALUES (?, ?, ?, ?)""",
            [(a["link"], a["title"], a["source"], a.get("published")) for a in articles],
        )
