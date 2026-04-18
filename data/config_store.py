import sqlite3
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent / "bot.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER PRIMARY KEY,
            permission_id INTEGER NOT NULL
        )
        """
    )


def get_config_value(key: str) -> Optional[str]:
    with _get_connection() as conn:
        _ensure_table(conn)
        row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def set_config_value(key: str, value: Optional[str]) -> None:
    with _get_connection() as conn:
        _ensure_table(conn)
        if value is None:
            conn.execute("DELETE FROM config WHERE key = ?", (key,))
        else:
            conn.execute(
                "INSERT INTO config(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
        conn.commit()
