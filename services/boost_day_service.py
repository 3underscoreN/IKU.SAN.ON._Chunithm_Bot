import logging
from datetime import date, datetime

import requests

from dotenv import dotenv_values

from data.models import BoostDayProposal

logger = logging.getLogger(__name__)

cfg = dotenv_values(".env")
WEB_API_URL_BASE = cfg.get("WEB_API_URL_BASE", "http://host.docker.internal:3000/api/v1")


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

