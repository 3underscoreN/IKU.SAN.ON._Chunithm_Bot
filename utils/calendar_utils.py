import calendar

USER_SELECTED_DATES_PRE='[0;34m'
USER_SELECTED_DATES_POST='[0m'

def render_calendar(year: int, month: int, highlight_days: list[int] = []) -> str:
  """Render a calendar for the given year and month, highlighting specified days."""
  cal = calendar.monthcalendar(year, month)
  lines = []

  header = calendar.month_name[month] + " " + str(year)
  days_of_week = "Mo Tu We Th Fr Sa Su"

  lines.append(header.center(20))
  lines.append(days_of_week.center(20))

  for week in cal:
    row = []
    for day in week:
      if day == 0:
        row.append("  ")  # Empty day
      elif day in highlight_days:
        row.append(f"{USER_SELECTED_DATES_PRE}{day:2}{USER_SELECTED_DATES_POST}")  # Highlighted day
      else:
        row.append(f"{day:2}")  # Regular day

    lines.append(" ".join(row))

  return "```ansi\n" + "\n".join(lines) + "\n```"