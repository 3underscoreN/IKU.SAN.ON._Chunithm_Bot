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

    

def get_role_permission(role_id: int) -> Optional[int]:
    """
    Get the permission ID for a Discord role.
    
    :param role_id: The Discord role ID
    :return: The permission ID (0-3), or None if not set
    """
    with _get_connection() as conn:
        _ensure_table(conn)
        row = conn.execute(
            "SELECT permission_id FROM role_permissions WHERE role_id = ?",
            (role_id,),
        ).fetchone()
        return int(row["permission_id"]) if row else None


def set_role_permission(role_id: int, perm_id: int) -> None:
    """
    Set the permission ID for a Discord role.
    
    :param role_id: The Discord role ID
    :param perm_id: The permission ID (0-3)
    """
    if perm_id < 0 or perm_id > 3:
        raise ValueError(f"Invalid permission ID: {perm_id}. Must be 0-3.")
    
    with _get_connection() as conn:
        _ensure_table(conn)
        conn.execute(
            """
            INSERT INTO role_permissions(role_id, permission_id)
            VALUES(?, ?)
            ON CONFLICT(role_id) DO UPDATE SET permission_id = excluded.permission_id
            """,
            (role_id, perm_id),
        )
        conn.commit()


def delete_role_permission(role_id: int) -> None:
    """
    Delete the permission entry for a Discord role.
    
    :param role_id: The Discord role ID
    """
    with _get_connection() as conn:
        _ensure_table(conn)
        conn.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
        conn.commit()


def get_all_role_permissions() -> dict[int, int]:
    """
    Get all role permission mappings.
    
    :return: Dictionary mapping role_id -> permission_id
    """
    with _get_connection() as conn:
        _ensure_table(conn)
        rows = conn.execute("SELECT role_id, permission_id FROM role_permissions").fetchall()
    
    result = {}
    for row in rows:
        try:
            role_id = int(row["role_id"])
            perm_id = int(row["permission_id"])
            result[role_id] = perm_id
        except ValueError:
            # Skip malformed entries
            pass
    
    return result