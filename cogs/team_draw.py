import asyncio
import datetime
import logging
import random
import re

import discord
from discord import app_commands
from discord.ext import commands, tasks

from data.config_store import get_config_value, set_config_value
from exceptions import team_draw_exceptions
from parser.team_course import get_team_course_scores
from utils.embed import error_embed, info_embed, warning_embed

logger = logging.getLogger("discord.bot.cogs.team_draw")

from typing import Optional

TD_DRAW_DATETIME_KEY = "team_draw.td_draw_datetime"
TD_DRAW_CHANNEL_ID_KEY = "team_draw.td_draw_channel_id"


class TeamDrawState:
    """
    Manages the state of the team draw, including the scheduled draw time and channel ID.
    """

    def __init__(self):
        initial_state = self._load_state()
        datetime_string = initial_state.get("td_draw_datetime", None)
        self._td_draw_datetime: Optional[datetime.datetime] = None
        if datetime_string:
            try:
                self._td_draw_datetime = datetime.datetime.fromisoformat(
                    datetime_string
                )
            except ValueError:
                logger.warning(
                    "Invalid persisted draw datetime in config table. Ignoring value."
                )

        if self._td_draw_datetime and self._td_draw_datetime < datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=8))
        ):
            self._td_draw_datetime = None

        self._td_draw_channel_id: Optional[int] = initial_state.get(
            "td_draw_channel_id", None
        )

    @property
    def td_draw_datetime(self) -> Optional[datetime.datetime]:
        """
        Returns the scheduled draw datetime, or None if not set.
        """
        return self._td_draw_datetime

    @td_draw_datetime.setter
    def td_draw_datetime(self, value: Optional[datetime.datetime]):
        self._td_draw_datetime = value
        self._save_state()

    @td_draw_datetime.getter
    def td_draw_datetime(self) -> Optional[datetime.datetime]:
        return self._td_draw_datetime

    @property
    def td_draw_channel_id(self) -> Optional[int]:
        return self._td_draw_channel_id

    @td_draw_channel_id.setter
    def td_draw_channel_id(self, value: Optional[int]):
        self._td_draw_channel_id = value
        self._save_state()

    @td_draw_channel_id.getter
    def td_draw_channel_id(self) -> Optional[int]:
        return self._td_draw_channel_id

    def _load_state(self):
        raw_channel_id = get_config_value(TD_DRAW_CHANNEL_ID_KEY)
        channel_id = None
        if raw_channel_id:
            try:
                channel_id = int(raw_channel_id)
            except ValueError:
                logger.warning(
                    "Invalid persisted draw channel id in config table. Ignoring value."
                )

        return {
            "td_draw_datetime": get_config_value(TD_DRAW_DATETIME_KEY),
            "td_draw_channel_id": channel_id,
        }

    def _save_state(self):
        set_config_value(
            TD_DRAW_DATETIME_KEY,
            self._td_draw_datetime.isoformat() if self._td_draw_datetime else None,
        )
        set_config_value(
            TD_DRAW_CHANNEL_ID_KEY,
            str(self._td_draw_channel_id)
            if self._td_draw_channel_id is not None
            else None,
        )

@app_commands.default_permissions(manage_roles=True)
class TeamDrawCog(commands.GroupCog, name="teamdraw"):
    state = TeamDrawState()

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_draw.start()

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Global error handler for app commands in this cog."""
        if isinstance(error, team_draw_exceptions.TeamDrawError):
            embed = error_embed(
                description=error.args[0].get("message"),
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.edit_original_response(embed=embed, view=None)
            return
        raise error  # Propagate to global handler if unhandled.

    @tasks.loop(
        time=state.td_draw_datetime.time()
        if state.td_draw_datetime
        else datetime.time(12, 34)
    )
    async def start_draw(self):
        logger.info("Starting team draw task...")
        print("Starting team draw task...")
        # see if today is the draw date
        now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

        if self.state.td_draw_datetime is None:
            logger.info("No draw date set. Skipping draw.")
            return

        if now.date() != self.state.td_draw_datetime.date():
            logger.info("Today is not the draw date. Skipping draw.")
            return

        if self.state.td_draw_channel_id is None:
            logger.warning("Draw channel ID is not set. Cannot perform draw.")
            return

        channel = self.bot.get_channel(self.state.td_draw_channel_id)
        if channel is None:
            logger.warning("Draw channel is invalid or not found.")
            return

        # perform the draw
        try:
            team_scores = await get_team_course_scores()
            if not team_scores:
                logger.warning("No team scores found for the draw.")
                return

            # Find the highest score
            players = list(team_scores.keys())
            scores = list(team_scores.values())

            winner = random.choices(players, weights=scores, k=1)[0]
            embed = info_embed(
                title="🎉 團員抽獎結果 🎉",
            )
            entries = "\n".join(
                [f"{player}: `{score}` 分" for player, score in team_scores.items()]
            )
            embed.add_field(
                name="抽獎時間", value=f"<t:{int(now.timestamp())}>", inline=False
            )
            embed.add_field(name="抽選名單：", value=entries, inline=False)
            embed.add_field(
                name="恭喜得獎者：", value=f"🎊 **{winner}** 🎊", inline=False
            )

            await channel.send(embed=embed)  # type:ignore

            logger.info("Team draw completed successfully.")
        except Exception as e:
            logger.error(f"Error during team draw: {e}")

        self.state.td_draw_datetime = None

    @app_commands.command(
        name="set_draw_time",
        description="設定團隊抽選的時間(UTC+8)。只有設定後才會進行抽選。",
    )
    @app_commands.describe(
        time="時間格式為YYYY-MM-DDTHH:MM:SS+08:00, 例如2024-12-31T15:00:00+08:00"
    )
    async def set_draw_time(self, interaction: discord.Interaction, time: str):
        date_re = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$"
        if not re.match(date_re, time):
            raise team_draw_exceptions.InvalidDrawTimeFormatException()

        if datetime.datetime.fromisoformat(time) <= datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=8))
        ):
            raise team_draw_exceptions.DrawTimeInPastException()

        self.state.td_draw_datetime = datetime.datetime.fromisoformat(time)
        self.start_draw.change_interval(
            time=self.state.td_draw_datetime.time().replace(
                tzinfo=datetime.timezone(datetime.timedelta(hours=8))
            )
        )
        self.start_draw.restart()

        embed = info_embed(
            description=f"已設定團隊抽選時間為 {self.state.td_draw_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')} (UTC+8)"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="set_draw_channel", description="設定團隊抽選的頻道")
    @app_commands.describe(channel="設定進行團隊抽選的頻道")
    async def set_draw_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        try:
            msg = await channel.send("這是一則測試訊息，用以確認頻道有效性。")
        except Exception:
            raise team_draw_exceptions.InvalidChannelException()

        await msg.delete()

        self.state.td_draw_channel_id = channel.id

        embed = info_embed(description=f"已設定團隊抽選頻道為 {channel.mention}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="view_settings", description="查看目前團隊抽選設定")
    async def view_settings(self, interaction: discord.Interaction):
        draw_time_str = (
            self.state.td_draw_datetime.strftime("%Y-%m-%d %H:%M:%S %Z")
            if self.state.td_draw_datetime
            else "未設定"
        )
        channel_mention = (
            f"<#{self.state.td_draw_channel_id}>"
            if self.state.td_draw_channel_id
            else "未設定"
        )

        embed = info_embed(
            title="團隊抽選設定",
            fields=[
                ("抽選時間", draw_time_str, False),
                ("抽選頻道", channel_mention, False),
            ],
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="cancel_draw", description="取消目前設定的團隊抽選")
    async def cancel_draw(self, interaction: discord.Interaction):
        self.state.td_draw_datetime = None

        embed = info_embed(description="已取消目前設定的團隊抽選。")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def add(bot: commands.Bot):
    cog = TeamDrawCog(bot)
    await bot.add_cog(cog)
