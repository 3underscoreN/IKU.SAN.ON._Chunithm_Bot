import logging
import sqlite3
from datetime import date, datetime

from data.db import db
from data.models import BoostDayProposal, BoostDayState

logger = logging.getLogger(__name__)


def add_proposal(user_id: int, target_date: date, month_key: str) -> BoostDayProposal:
    """Add a user's boost day proposal for a month (allows multiple per user, no exact duplicates)."""
    now = datetime.now()

    with db.get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO boost_day_proposals (user_id, target_date, month_key, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, target_date, month_key, now, now),
            )
            conn.commit()
        except sqlite3.IntegrityError as exc:  # duplicate per user/month/date
            raise exc

        inserted_id = cursor.lastrowid
        cursor.execute(
            "SELECT id, user_id, target_date, month_key, created_at, updated_at FROM boost_day_proposals WHERE id = ?",
            (inserted_id,),
        )
        row = cursor.fetchone()

        return BoostDayProposal(
            id=row[0],
            user_id=row[1],
            target_date=date.fromisoformat(row[2]),
            month_key=row[3],
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5]),
        )


def get_user_proposals(user_id: int, month_key: str) -> list[BoostDayProposal]:
    """Retrieve all proposals for a user in a specific month (ordered by creation)."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, user_id, target_date, month_key, created_at, updated_at
            FROM boost_day_proposals
            WHERE user_id = ? AND month_key = ?
            ORDER BY created_at
            """,
            (user_id, month_key),
        )
        rows = cursor.fetchall()

        return [
            BoostDayProposal(
                id=row[0],
                user_id=row[1],
                target_date=date.fromisoformat(row[2]),
                month_key=row[3],
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5]),
            )
            for row in rows
        ]


def get_month_proposals(month_key: str) -> list[BoostDayProposal]:
    """Retrieve all proposals for a specific month."""
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, target_date, month_key, created_at, updated_at FROM boost_day_proposals WHERE month_key = ? ORDER BY created_at",
            (month_key,)
        )
        rows = cursor.fetchall()
        
        return [
            BoostDayProposal(
                id=row[0],
                user_id=row[1],
                target_date=date.fromisoformat(row[2]),
                month_key=row[3],
                created_at=datetime.fromisoformat(row[4]),
                updated_at=datetime.fromisoformat(row[5])
            )
            for row in rows
        ]


def lock_month(month_key: str) -> BoostDayState:
    """Lock a month for voting (transition from open to voting)."""
    now = datetime.now()
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        
        # Check if state exists
        cursor.execute("SELECT id FROM boost_day_state WHERE month_key = ?", (month_key,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE boost_day_state SET status = 'voting', updated_at = ? WHERE month_key = ?",
                (now, month_key)
            )
        else:
            cursor.execute(
                "INSERT INTO boost_day_state (month_key, status, created_at, updated_at) VALUES (?, 'voting', ?, ?)",
                (month_key, now, now)
            )
        
        conn.commit()
        
        # Fetch and return the state
        cursor.execute(
            "SELECT id, month_key, status, winning_date, created_at, updated_at FROM boost_day_state WHERE month_key = ?",
            (month_key,)
        )
        row = cursor.fetchone()
        
        return BoostDayState(
            id=row[0],
            month_key=row[1],
            status=row[2],
            winning_date=date.fromisoformat(row[3]) if row[3] else None,
            created_at=datetime.fromisoformat(row[4]),
            updated_at=datetime.fromisoformat(row[5])
        )
