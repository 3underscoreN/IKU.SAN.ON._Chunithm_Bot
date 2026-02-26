import requests
from dotenv import dotenv_values

import logging

cfg = dotenv_values(".env")
WEB_API_URL_BASE = f"{cfg.get("WEB_URL_BASE", "http://host.docker.internal:3000")}/api/v1"

logger = logging.getLogger(__name__)


async def get_token(userid: str) -> str | None:
    """Fetch an authentication token for a given user ID, or None if the request fails."""
    print(userid)
    response = requests.post(f"{WEB_API_URL_BASE}/internal/auth/tokengen", json={"userId": userid})

    if response.status_code != 200:
        logger.error(f"Failed to fetch token: {response.status_code} {response.text}")
        return None
    
    data = response.json()
    
    return data.get("token")