import sqlite3

DB_PATH = "research_history.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    TEXT    NOT NULL DEFAULT 'legacy',
            query      TEXT    NOT NULL,
            depth      TEXT    NOT NULL,
            report     TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Migrate existing DBs that don't have user_id yet
    try:
        conn.execute("ALTER TABLE reports ADD COLUMN user_id TEXT NOT NULL DEFAULT 'legacy'")
    except Exception:
        pass
    conn.commit()
    conn.close()


def save_report(user_id: str, query: str, depth: str, report: str) -> int:
    conn = _connect()
    cursor = conn.execute(
        "INSERT INTO reports (user_id, query, depth, report) VALUES (?, ?, ?, ?)",
        (user_id, query, depth, report),
    )
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def get_history(user_id: str, limit: int = 15) -> list[dict]:
    conn = _connect()
    cursor = conn.execute(
        "SELECT id, query, depth, report, created_at FROM reports "
        "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit),
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


def delete_report(report_id: int, user_id: str):
    conn = _connect()
    # user_id check prevents one user deleting another's report
    conn.execute("DELETE FROM reports WHERE id = ? AND user_id = ?", (report_id, user_id))
    conn.commit()
    conn.close()
