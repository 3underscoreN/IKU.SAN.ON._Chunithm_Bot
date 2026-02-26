import logging
from datetime import date, datetime

import requests

from dotenv import dotenv_values

from data.models import BoostDayProposal

logger = logging.getLogger(__name__)

cfg = dotenv_values(".env")
WEB_API_URL_BASE = f"{cfg.get("WEB_API_URL_BASE", "http://host.docker.internal:3000/api/v1")}"

# def add_proposal(user_id: int, target_date: date, month_key: str) -> BoostDayProposal:
#     """Add a user's boost day proposal for a month (allows multiple per user, no exact duplicates)."""
#     now = datetime.now()

#     with db.get_connection() as conn:
#         cursor = conn.cursor()
#         try:
#             cursor.execute(
#                 """
#                 INSERT INTO boost_day_proposals (user_id, target_date, month_key, created_at, updated_at)
#                 VALUES (?, ?, ?, ?, ?)
#                 """,
#                 (user_id, target_date, month_key, now, now),
#             )
#             conn.commit()
#         except sqlite3.IntegrityError as exc:  # duplicate per user/month/date
#             raise exc

#         inserted_id = cursor.lastrowid
#         cursor.execute(
#             "SELECT id, user_id, target_date, month_key, created_at, updated_at FROM boost_day_proposals WHERE id = ?",
#             (inserted_id,),
#         )
#         row = cursor.fetchone()

#         return BoostDayProposal(
#             id=row[0],
#             user_id=row[1],
#             target_date=date.fromisoformat(row[2]),
#             month_key=row[3],
#             created_at=datetime.fromisoformat(row[4]),
#             updated_at=datetime.fromisoformat(row[5]),
#         )


async def get_user_proposals(user_id: int, month_key: str) -> list[BoostDayProposal]:
    """Retrieve all proposals for a user in a specific month (ordered by creation)."""
    year, month = month_key.split("-")
    response = requests.get(f"{WEB_API_URL_BASE}/internal/boostday/viewuser", params={"userId": str(user_id), "year": year, "month": month})

    if response.status_code != 200:
        logger.error(f"Failed to fetch user proposals: {response.status_code} {response.text}")
        return []
    
    data = response.json().get("data", [])

    return list(map(lambda p: BoostDayProposal(
        user_id=user_id,
        target_date=datetime.fromisoformat(p["date"]).date(),
        month_key=month_key,
        created_at=datetime.fromisoformat(p["createdAt"]),
    ), data))


async def get_month_proposals(month_key: str) -> list[BoostDayProposal]:
    """Retrieve all proposals for a specific month."""
    year, month = month_key.split("-")
    response = requests.get(f"{WEB_API_URL_BASE}/internal/boostday/viewall", params={"year": year, "month": month})

    if response.status_code != 200:
        logger.error(f"Failed to fetch month proposals: {response.status_code} {response.text}")
        return []
    
    data = response.json().get("data", [])

    return list(map(lambda p: BoostDayProposal(
        user_id=p["userId"],
        target_date=datetime.fromisoformat(p["date"]).date(),
        month_key=month_key,
        created_at=datetime.fromisoformat(p["createdAt"]),
    ), data))


# def remove_proposal(user_id: int, target_date: date, month_key: str) -> bool:
#     """Remove a specific proposal for a user in a month.

#     Returns True if a row was deleted, False otherwise.
#     """
#     with db.get_connection() as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             "DELETE FROM boost_day_proposals WHERE user_id = ? AND target_date = ? AND month_key = ?",
#             (user_id, target_date, month_key),
#         )
#         conn.commit()

#         return cursor.rowcount > 0


# def lock_month(month_key: str) -> BoostDayState:
#     """Lock a month for voting (transition from open to voting)."""
#     now = datetime.now()
    
#     with db.get_connection() as conn:
#         cursor = conn.cursor()
        
#         # Check if state exists
#         cursor.execute("SELECT id FROM boost_day_state WHERE month_key = ?", (month_key,))
#         existing = cursor.fetchone()
        
#         if existing:
#             cursor.execute(
#                 "UPDATE boost_day_state SET status = 'voting', updated_at = ? WHERE month_key = ?",
#                 (now, month_key)
#             )
#         else:
#             cursor.execute(
#                 "INSERT INTO boost_day_state (month_key, status, created_at, updated_at) VALUES (?, 'voting', ?, ?)",
#                 (month_key, now, now)
#             )
        
#         conn.commit()
        
#         # Fetch and return the state
#         cursor.execute(
#             "SELECT id, month_key, status, winning_date, created_at, updated_at FROM boost_day_state WHERE month_key = ?",
#             (month_key,)
#         )
#         row = cursor.fetchone()
        
#         return BoostDayState(
#             id=row[0],
#             month_key=row[1],
#             status=row[2],
#             winning_date=date.fromisoformat(row[3]) if row[3] else None,
#             created_at=datetime.fromisoformat(row[4]),
#             updated_at=datetime.fromisoformat(row[5])
#         )
