import discord
from discord import app_commands
from discord.ext import commands, tasks

import re

import random

from parser.team_point import get_team_scores
from exceptions import team_draw_exceptions
from utils.embed import error_embed, info_embed, warning_embed

import datetime
import json
import asyncio

import logging

logger = logging.getLogger(__name__)

from typing import Optional

STATE_FILE = 'data/_team_draw_state.json'

def _load_state():
  try:
    with open(STATE_FILE, 'r') as f:
      return json.load(f)
  except FileNotFoundError:
    return {}

def _save_state(td_draw_datetime: datetime.datetime, td_draw_channel_id: int):
  with open(STATE_FILE, 'w') as f:
    json.dump({
      'td_draw_datetime': td_draw_datetime.isoformat(),
      'td_draw_channel_id': td_draw_channel_id 
    }, f)

class TeamDrawCog(commands.GroupCog, name='teamdraw'):

  states = _load_state()
  td_draw_datetime_str: Optional[str] = states.get('td_draw_datetime', None)
  td_draw_datetime: Optional[datetime.datetime] = datetime.datetime.fromisoformat(td_draw_datetime_str) if td_draw_datetime_str else None

  td_draw_channel_id: Optional[int] = states.get('td_draw_channel_id', None)

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Global error handler for app commands in this cog."""
    if isinstance(error, team_draw_exceptions.TeamDrawError):
      embed = error_embed(
        description=error.args[0].get('message'),
      )
      if not interaction.response.is_done():
        await interaction.response.send_message(embed=embed, ephemeral=True)
      else:
        await interaction.edit_original_response(embed=embed, view=None)

      return
    
    raise error  # Propagate to global handler if unhandled.

  @tasks.loop(time=td_draw_datetime.time() if td_draw_datetime else datetime.datetime.min.time())
  async def start_draw(self):
    logger.info('Starting team draw task...')
    # see if today is the draw date
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

    if self.td_draw_datetime is None:
      return
    
    if now.date() != self.td_draw_datetime.date():
      logger.info('Today is not the draw date. Skipping draw.')
      return
    
    if self.td_draw_channel_id is None:
      logger.error('Draw channel ID is not set. Cannot perform draw.')
      return

    channel = self.bot.get_channel(self.td_draw_channel_id)
    if channel is None or not isinstance(channel, discord.TextChannel):
      logger.error('Draw channel is invalid or not found.')
      return
    
    # perform the draw
    try:
      team_scores = await get_team_scores()
      if not team_scores:
        logger.warning('No team scores found for the draw.')
        return

      # Find the highest score
      players = list(team_scores.keys())
      scores = list(team_scores.values())

      winner = random.choices(players, weights=scores, k=1)[0]
      embed = info_embed(
        title="🎉 團員抽獎結果 🎉",
      )
      entries = "\n".join([f"{player}: `{score}` 分" for player, score in team_scores.items()])
      embed.add_field(name="抽選名單：", value=entries, inline=False)
      embed.add_field(name="恭喜得獎者：", value=f"🎊 **{winner}** 🎊", inline=False)
      await channel.send(embed=embed)

      logger.info('Team draw completed successfully.')
    except Exception as e:
      logger.error(f'Error during team draw: {e}')

    self.td_draw_datetime = None
    _save_state(self.td_draw_datetime or datetime.datetime.min, self.td_draw_channel_id or 0)
    self.start_draw.cancel() # stop the task
    
  @app_commands.command(name="set_draw_time", description="設定團隊抽選的時間(UTC+8)。只有設定後才會進行抽選。")
  @app_commands.describe(time="時間格式為YYYY-MM-DDTHH:MM:SS+08:00, 例如2024-12-31T15:00:00+08:00")
  async def set_draw_time(self, interaction: discord.Interaction, time: str):
    date_re = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$'
    if not re.match(date_re, time):
      raise team_draw_exceptions.InvalidDrawTimeFormatException()
    
    if datetime.datetime.fromisoformat(time) <= datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))):
      raise team_draw_exceptions.DrawTimeInPastException()
    
    self.td_draw_datetime = datetime.datetime.fromisoformat(time)
    _save_state(self.td_draw_datetime, self.td_draw_channel_id or 0)

    # Restart the task with the new time
    if self.start_draw.is_running():
      self.start_draw.stop()

    self.start_draw.change_interval(time=self.td_draw_datetime.time())
    self.start_draw.start()
    embed = info_embed(
      description=f"已設定團隊抽選時間為 {self.td_draw_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC+8)"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

  @app_commands.command(name="set_draw_channel", description="設定團隊抽選的頻道")
  @app_commands.describe(channel="設定進行團隊抽選的頻道")
  async def set_draw_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
    try:
      msg = await channel.send("這是一則測試訊息，用以確認頻道有效性。")
    except Exception:
      raise team_draw_exceptions.InvalidChannelException()
    
    await msg.delete()

    self.td_draw_channel_id = channel.id
    _save_state(self.td_draw_datetime or datetime.datetime.min, self.td_draw_channel_id)

    embed = info_embed(
      description=f"已設定團隊抽選頻道為 {channel.mention}"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

  @app_commands.command(name="view_settings", description="查看目前團隊抽選設定")
  async def view_settings(self, interaction: discord.Interaction):
    draw_time_str = self.td_draw_datetime.strftime('%Y-%m-%d %H:%M:%S %Z') if self.td_draw_datetime else "未設定"
    channel_mention = f"<#{self.td_draw_channel_id}>" if self.td_draw_channel_id else "未設定"

    embed = info_embed(
      title="團隊抽選設定",
      fields=[
        ("抽選時間", draw_time_str, False),
        ("抽選頻道", channel_mention, False)
      ]
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

  @app_commands.command(name="cancel_draw", description="取消目前設定的團隊抽選")
  async def cancel_draw(self, interaction: discord.Interaction):
    self.td_draw_datetime = None
    _save_state(self.td_draw_datetime or datetime.datetime.min, self.td_draw_channel_id or 0)

    if self.start_draw.is_running():
      self.start_draw.stop()

    embed = info_embed(
      description="已取消目前設定的團隊抽選。"
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

async def add(bot: commands.Bot):
  cog = TeamDrawCog(bot)
  await bot.add_cog(cog)
