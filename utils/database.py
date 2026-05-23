import sqlite3
from datetime import datetime

DB_PATH = "research_history.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            query     TEXT    NOT NULL,
            depth     TEXT    NOT NULL,
            report    TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def save_report(query: str, depth: str, report: str) -> int:
    conn = _connect()
    cursor = conn.execute(
        "INSERT INTO reports (query, depth, report) VALUES (?, ?, ?)",
        (query, depth, report),
    )
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_history(limit: int = 10) -> list[dict]:
    conn = _connect()
    cursor = conn.execute(
        "SELECT id, query, depth, report, created_at FROM reports ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_report(report_id: int) -> dict | None:
    conn = _connect()
    cursor = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def delete_report(report_id: int):
    conn = _connect()
    conn.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()
