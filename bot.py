import logging
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from cogs.boost_day import add as boost_day_setup

import sqlite3

from data.db import db


load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
# intents.message_content = True
# intents.members = True


class ChunithmBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self) -> None:
        # Initialize database on startup.
        db.init_db()

        # Load cogs.
        await boost_day_setup(self)

        # Sync application (slash) commands on startup.
        await self.tree.sync()

bot = ChunithmBot()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")


@bot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)