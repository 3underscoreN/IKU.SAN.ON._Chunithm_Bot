# import sqlite3
# import logging
# from pathlib import Path
# from contextlib import contextmanager

# logger = logging.getLogger(__name__)

# DB_PATH = Path(__file__).parent / "bot.db"


# class Database:
#     """SQLite database manager for the bot."""

#     def __init__(self, db_path: Path = DB_PATH):
#         self.db_path = db_path
#         self._initialized = False

#     def init_db(self) -> None:
#         """Initialize database schema if not already done."""
#         if self._initialized:
#             return

#         with self.get_connection() as conn:
#             cursor = conn.cursor()

#             # Check existing schema for boost_day_proposals to handle old UNIQUE constraint.
#             cursor.execute(
#                 "SELECT sql FROM sqlite_master WHERE type='table' AND name='boost_day_proposals'"
#             )
#             existing_sql = cursor.fetchone()

#             # Desired schema: allow multiple proposals per user per month, but prevent exact duplicates per date.
#             # Constraint: UNIQUE(user_id, month_key, target_date)
#             desired_sql_snippet = "UNIQUE(user_id, month_key, target_date)"

#             def create_proposals_table():
#                 cursor.execute(
#                     """
#                     CREATE TABLE IF NOT EXISTS boost_day_proposals (
#                         id INTEGER PRIMARY KEY AUTOINCREMENT,
#                         user_id INTEGER NOT NULL,
#                         target_date DATE NOT NULL,
#                         month_key TEXT NOT NULL,
#                         created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                         updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                         UNIQUE(user_id, month_key, target_date)
#                     )
#                     """
#                 )

#             if not existing_sql:
#                 create_proposals_table()
#             else:
#                 current_sql = existing_sql[0] or ""
#                 if desired_sql_snippet not in current_sql:
#                     # Migrate: remove old constraint or no constraint; rebuild with desired unique on (user_id, month_key, target_date)
#                     cursor.execute("ALTER TABLE boost_day_proposals RENAME TO boost_day_proposals_old")
#                     create_proposals_table()
#                     cursor.execute(
#                         """
#                         INSERT OR IGNORE INTO boost_day_proposals (user_id, target_date, month_key, created_at, updated_at)
#                         SELECT user_id, target_date, month_key, created_at, updated_at FROM boost_day_proposals_old
#                         """
#                     )
#                     cursor.execute("DROP TABLE boost_day_proposals_old")

#             # Boost day proposals table ensured above

#             # Boost day votes table
#             cursor.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS boost_day_votes (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     month_key TEXT NOT NULL,
#                     user_id INTEGER NOT NULL,
#                     voted_date DATE NOT NULL,
#                     created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                     UNIQUE(month_key, user_id)
#                 )
#                 """
#             )

#             # Boost day state tracking
#             cursor.execute(
#                 """
#                 CREATE TABLE IF NOT EXISTS boost_day_state (
#                     id INTEGER PRIMARY KEY AUTOINCREMENT,
#                     month_key TEXT UNIQUE NOT NULL,
#                     status TEXT NOT NULL DEFAULT 'open',
#                     winning_date DATE,
#                     created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#                     updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
#                 )
#                 """
#             )

#             conn.commit()
#             self._initialized = True
#             logger.info(f"Database initialized at {self.db_path}")

#     @contextmanager
#     def get_connection(self):
#         """Context manager for database connections."""
#         conn = sqlite3.connect(str(self.db_path))
#         conn.row_factory = sqlite3.Row
#         try:
#             yield conn
#         finally:
#             conn.close()


# # Global database instance
# db = Database()
