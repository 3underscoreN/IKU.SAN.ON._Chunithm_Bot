import calendar
from PIL import Image, ImageDraw, ImageFont
import datetime    

import io

from typing import Mapping

import math

font = ImageFont.truetype("assets/GoogleSans.ttf", 32)
font_count = ImageFont.truetype("assets/GoogleSans.ttf", 22)
win_image = Image.open("assets/chiiwawa_think.webp").resize((48, 48))
cell = 120
padding = 40
header_height = 40
border_width = 4

bg_color = (49, 51, 56)
text_color = (220, 221, 222)
border_color = (100, 100, 100) # lighter gray for calendar borders

# for self view
mark_color = (88, 101, 242) # blurpl-ish color for marked days

# for all view
min_color = (49, 51, 56) # same as background color for minimum count
max_color = (77, 204, 142) # ralsei green for maximum count
text_color_on_max = (23, 23, 23) # dark text color for better contrast on max color

cal = calendar.Calendar(firstweekday=0)
weekdays = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

def powernorm(value: float, min: float, max: float, gamma: float = 0.5) -> float:
  """
  Normalize a value using a power function.

  @param value: The value to be normalized.
  @param max: The maximum possible value for normalization.
  @param gamma: The exponent to be applied to the normalized value (default is 0.5).
  @return: The normalized value after applying the power function.
  """
  if gamma <= 0 or gamma > 1:
    raise ValueError("Gamma must be in the range (0, 1]")
  if max == 0:
    return 0
  normalized = (value - min) / (max - min)
  return math.pow(normalized, gamma)

def colornorm(min_color: tuple[int], max_color: tuple[int], multiplier: float) -> tuple[int]:
  """
  Normalize a value to a color intensity (0-255).

  @param value: The value to be normalized.
  @param min_color: The minimum possible color values for normalization.
  @param max_color: The maximum possible color values for normalization.
  @param multiplier: A multiplier to adjust the normalized value.
  @return: The normalized color intensity as an integer between 0 and 255.
  """
  if multiplier < 0 or multiplier > 1:
    raise ValueError("Multiplier must be in the range (0, 1]")
  if multiplier == 0:
    return min_color
  
  return tuple(int(min_c + (max_c - min_c) * multiplier) for min_c, max_c in zip(min_color, max_color))

def generate_self_calendar(year: int, month: int, marked_days: set[int]) -> io.BytesIO:
    """
    Generate a calendar image for the specified year and month, marking the specified days.
    
    @param year: The year for which to generate the calendar.
    @param month: The month for which to generate the calendar.
    @param marked_days: A set of day numbers to be marked on the calendar.
    @return: A BytesIO object containing the generated calendar image in PNG format.
    """
    global font, cell, padding, header_height, border_width
    global bg_color, text_color, border_color, mark_color
    global weekdays, cal

    
    month_days = cal.monthdayscalendar(year, month)

    width = cell * 7 + padding * 2
    height = cell * len(month_days) + padding * 2 + header_height

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

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

            draw.text((x1 + 10, y1 + 10), str(day), fill=text_color, font=font)
            
    generated_at = datetime.datetime.now(tz=datetime.timezone(offset=datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    draw.text((width - padding - len(generated_at) * 14, height - padding - 10), generated_at, fill=text_color, font=font_count)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def generate_all_calendar(year: int, month: int, count_of_days: Mapping[int, int]) -> io.BytesIO:
    """
    Generate a calendar image for the specified year and month, marking the specified days.
    
    @param year: The year for which to generate the calendar.
    @param month: The month for which to generate the calendar.
    @param count_of_days: A mapping of day numbers to counts, indicating how many entries are received for each day.
    @return: A BytesIO object containing the generated calendar image in PNG format.
    """
    global font, cell, padding, header_height, border_width
    global bg_color, text_color, border_color, mark_color, min_color, max_color
    global weekdays, cal

    month_days = cal.monthdayscalendar(year, month)

    # check if there are missing days in the count_of_days mapping
    for week in month_days:
        for day in week:
            if day != 0 and day not in count_of_days:
                count_of_days[day] = 0

    width = cell * 7 + padding * 2
    height = cell * len(month_days) + padding * 2 + header_height

    count_values_sorted = sorted(count_of_days.values(), reverse=True)

    min_count = min(count_of_days.values())
    max_count = count_values_sorted[0]
    count_of_days_norm = {day: powernorm(count, min_count, max_count, 0.3) for day, count in count_of_days.items()}

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

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

            count = count_of_days[day]
            this_text_color = text_color
            if count > 0:
                # normalize the count to a value between 0 and 1 using powernorm, then get the corresponding color intensity using colornorm
                color_intensity = count_of_days_norm[day]
                color = colornorm(min_color, max_color, color_intensity)
                this_text_color = text_color_on_max if color_intensity > 0.7 else text_color
                draw.rectangle([x1, y1, x2, y2], fill=color)

            draw.rectangle([x1, y1, x2, y2], outline=border_color, width=border_width) # border

            draw.text((x1 + 10 + border_width, y1 + 10 + border_width), str(day), fill=this_text_color, font=font) # calendar day number

            if count > 0 and count in count_values_sorted[:2]: # top 2 counts get the win image
                img.paste(win_image, (x1 + cell - 48, y1 + cell - 48), win_image) # win image for max count

            draw.text((x1 + cell - 48 + 16, y1 + cell - 48 - 16), f"{str(count)}", fill=this_text_color, font=font_count) # count text

    # TODO: Add generated at at bottom right
    generated_at = datetime.datetime.now(tz=datetime.timezone(offset=datetime.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
    draw.text((width - padding - len(generated_at) * 10, height - padding + 4), generated_at, fill=text_color, font=font_count)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    year, month = 2026, 3
    # test all_calendar
    import random
    random.seed(42)

    # test case 1: clustered counts
    count_of_days1 = {i : random.randint(4, 6) for i in range(1, 32)}

    # test case 2: sparsed counts
    count_of_days2 = {i: random.randint(0, 20) for i in range(1, 32)}

    # test case 3: all zero counts
    count_of_days3 = {i: 0 for i in range(1, 32)}

    # test case 4: outliers
    count_of_days4 = {i: random.randint(0, 5) for i in range(1, 32)}
    count_of_days4[5] = 50
    count_of_days4[15] = 30

    buffer1 = generate_all_calendar(year, month, count_of_days1)
    buffer2 = generate_all_calendar(year, month, count_of_days2)
    buffer3 = generate_all_calendar(year, month, count_of_days3)
    buffer4 = generate_all_calendar(year, month, count_of_days4)

    with open("test_calendar1.png", "wb") as f:
        f.write(buffer1.getbuffer())
    with open("test_calendar2.png", "wb") as f:
        f.write(buffer2.getbuffer())
    with open("test_calendar3.png", "wb") as f:
        f.write(buffer3.getbuffer())
    with open("test_calendar4.png", "wb") as f:
        f.write(buffer4.getbuffer())
