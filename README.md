# IKU.SAN.ON._Chunithm_Bot

Discord bot for Chunithm utilities. Current branch focuses on boost-day scheduling with slash commands and SQLite persistence.

## Features (current)
- Slash commands:
	- `/boostday propose YYYY-MM-DD` — propose a boost day date (future dates, current or next month; blocks current-month proposals after the 15th; duplicate same-date per user/month rejected).
	- `/boostday view_self [YYYY-MM]` — list all your proposals for the month (defaults to current month).
	- `/boostday view_all [YYYY-MM]` — list all proposals for the month (defaults to current month).
    - `/teampoint set_channel CHANNEL` — decide which channel to interact this service with
    - `/teampoint update` — list all team members and their team points
- Persistence:
	- SQLite `data/bot.db` auto-initialized on startup.
	- Tables: proposals (unique per user/month/date), votes (one vote per user/month), state (per-month status + winning date placeholder).

## Setup
1) Python 3.11+ recommended.
2) Install dependencies: `pip install -r requirements.txt`
3) Create `.env` with:
	 - `DISCORD_TOKEN=your_bot_token`
     - `PARSER_SEGA_ID=your_sega_account`
     - `PARSER_SEGA_PW=your_sega_password`
4) Run the bot: `python bot.py`

## Notes
- Database lives at `data/bot.db` and is created/migrated automatically.
- Multiple distinct dates per user per month are allowed; identical duplicates are blocked.