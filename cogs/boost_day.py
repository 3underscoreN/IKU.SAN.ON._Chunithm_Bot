import discord
from discord import app_commands
from discord.ext import commands

from datetime import date

from utils.date_utils import parse_iso_date, next_month, is_month_key_format
from utils.embed import error_embed, info_embed
from utils.calendar_image_utils import generate_self_calendar, generate_all_calendar

from services.web_auth_service import get_token
from services.boost_day_service import get_user_proposals, get_month_proposals

from exceptions import boost_day_exceptions

import logging

from dotenv import dotenv_values

WEB_URL_BASE = f"{dotenv_values('.env').get('WEB_URL_BASE', 'http://localhost:3000')}"

CUT_OFF_DAY = 15  # Mid-month cutoff for current-month proposals.
logger = logging.getLogger(__name__)

class BoostDayCog(commands.GroupCog, name='boostday'):
  def __init__(self, bot: commands.Bot):
    self.bot = bot

  async def month_key_parser(self, month: str | None) -> str:
    """Parse month key from input or default to current month."""
    today = date.today()
    
    if month is None:
      month_key = f"{today.year}-{today.month:02d}"
    else:
      if not is_month_key_format(month):
        raise boost_day_exceptions.InvalidMonthFormatException()
      month_key = month
    
    return month_key

  async def cog_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError) -> None:
    """Global error handler for app commands in this cog."""

    if isinstance(error, boost_day_exceptions.BoostDayError):
      embed = error_embed(
        description=error.args[0].get("message", "執行指令時發生錯誤，請檢查輸入並重試。")
      )

      if not interaction.response.is_done():
        await interaction.response.send_message(embed=embed, ephemeral=True)
      else:
        await interaction.edit_original_response(embed=embed, view=None)

      return
    
    raise error  # Propagate to global handler if unhandled.

  @app_commands.command(
    name='get_propose_link',
    description='獲取提案加成日鏈接。'
  )
  async def boost_day_get_propose_link(self, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    token = await get_token(str(interaction.user.id))
    if token is None:
      raise boost_day_exceptions.TokenFetchException()

    propose_url = f"{WEB_URL_BASE}/input/{token}"
    embed = info_embed(
      title="加成日提案鏈接",
      description=f"點擊以下鏈接前往提案頁面：{propose_url}",
    )
    embed.add_field(name="提示", value="請在30分鐘内完成提交，否則鏈接將失效。", inline=False)
    await interaction.followup.send(embed=embed, ephemeral=True)

  @app_commands.command(
    name='view_self',
    description='查看自己在指定月份的所有加成日提案 。'
  )
  @app_commands.rename(month="月份")
  @app_commands.describe(month="欲查詢的月份，格式為 YYYY-MM，預設為本月")
  async def my_boost_proposals(self, interaction: discord.Interaction, month: str = None):
    await interaction.response.defer(ephemeral=True)

    month_key = await self.month_key_parser(month if month else f"{date.today().year}-{date.today().month:02d}")
    
    proposals = await get_user_proposals(interaction.user.id, month_key)

    if not proposals:
      embed = info_embed(
        title="沒有加成日提案",
        description=f"您在 {month_key} 沒有任何加成日提案。",
        color=discord.Color.blue()
      )
      await interaction.followup.send(embed=embed, ephemeral=True)
      return

    year, month = map(int, month_key.split('-'))
    highlight_days = [p.target_date.day for p in proposals]

    calendar_png = generate_self_calendar(year, month, set(highlight_days))
    calendar_file = discord.File(calendar_png, filename="calendar.png")

    embed = info_embed(
        title=f"你的加成日提案：{month_key}",
        description=f"請查看以下日曆圖。\n藍色框選的日期為你已提案的日期。",
    )
    embed.set_image(url=f"attachment://{calendar_file.filename}")
  
    await interaction.followup.send(embed=embed, file=calendar_file, ephemeral=True)
    
  @app_commands.command(
    name='view_all',
    description='查看指定月份的所有加成日提案 。'
  )
  @app_commands.rename(month="月份")
  @app_commands.describe(month="欲查詢的月份，格式為 YYYY-MM，預設為本月")
  async def boost_proposals(self, interaction: discord.Interaction, month: str = None):
    month_key = await self.month_key_parser(month)

    proposals = await get_month_proposals(month_key)
    
    if not proposals:
      embed = info_embed(
        title="沒有加成日提案",
        description=f"{month_key} 沒有任何加成日提案。",
        color=discord.Color.blue()
      )
    else:
      count_of_days = {}
      for p in proposals:
        day = p.target_date.day
        count_of_days[day] = count_of_days.get(day, 0) + 1

      year, month = map(int, month_key.split('-'))
      calendar_png = generate_all_calendar(year, month, count_of_days)
      calendar_file = discord.File(calendar_png, filename="calendar.png")

      count_sorted_top_3 = sorted(count_of_days.items(), key=lambda x: x[1], reverse=True)[0:2]

      embed = info_embed(
        title=f"{month_key} 的加成日提案統計",
        description="請查看以下日曆圖。\n綠色越深的日期表示該日期的提案數量越多。",
        fields=[
          ("説明", "日曆圖中綠色越亮的日期表示該日期的提案數量越多。\n日曆中右上方的數字表示該日期的提案數量。\n帶有吉娃娃圖標的日期表示該日期的提案數量在本月排名前2。", False),
        ]
      )
      embed.set_image(url=f"attachment://{calendar_file.filename}")
      
    await interaction.response.send_message(embed=embed, file=calendar_file, ephemeral=True)

async def add(bot: commands.Bot):
  await bot.add_cog(BoostDayCog(bot))

async def remove(bot: commands.Bot):
  await bot.remove_cog("BoostDayCog")