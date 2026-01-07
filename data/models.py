from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class BoostDayProposal:
    """Represents a user's boost day date proposal."""
    user_id: int
    target_date: date
    month_key: str  # Format: "YYYY-MM"
    created_at: datetime
    updated_at: datetime
    id: int = None

@dataclass
class BoostDayVote:
    """Represents a user's vote during boost day voting period."""
    month_key: str  # Format: "YYYY-MM"
    user_id: int
    voted_date: date
    created_at: datetime
    id: int = None


@dataclass
class BoostDayState:
    """Tracks the state of a boost day month."""
    month_key: str  # Format: "YYYY-MM"
    status: str  # 'open', 'voting', 'closed'
    created_at: datetime
    updated_at: datetime
    winning_date: date = None
    id: int = None
    