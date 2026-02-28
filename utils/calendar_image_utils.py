import calendar
from PIL import Image, ImageDraw, ImageFont    

import io

font = ImageFont.truetype("assets/GoogleSans.ttf", 32)

def generate_calendar(year: int, month: int, marked_days: set[int]) -> io.BytesIO:
    """Generate a calendar image for the specified year and month, marking the specified days."""
    global font
    cell = 120
    padding = 40
    header_height = 40
    border_width = 4

    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    width = cell * 7 + padding * 2
    height = cell * len(month_days) + padding * 2 + header_height

    bg_color = (49, 51, 56)
    text_color = (220, 221, 222)
    border_color = (100, 100, 100) # lighter gray for calendar borders
    mark_color = (88, 101, 242) # blurpl-ish color for marked days

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
    for i, day_name in enumerate(weekdays):
        x = padding + i * cell
        y = header_height
        draw.text((x, y), day_name, fill=text_color, font=font)

    for row_idx, week in enumerate(month_days):
        for col_idx, day in enumerate(week):
            if day == 0:
                continue

            x1 = padding + col_idx * cell - border_width // 2
            y1 = header_height + padding + row_idx * cell - border_width // 2
            x2 = x1 + cell + border_width
            y2 = y1 + cell + border_width

            if day in marked_days:
                draw.rectangle([x1, y1, x2, y2], fill=mark_color)

            draw.rectangle([x1, y1, x2, y2], outline=border_color, width=border_width)

            draw.text((x1 + 10 + border_width // 2, y1 + 10 + border_width // 2), str(day), fill=text_color, font=font)
            
            # circle mark for specified days
            

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

