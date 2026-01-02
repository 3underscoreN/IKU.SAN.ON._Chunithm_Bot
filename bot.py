import logging
import os
from datetime import date

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import sqlite3

from utils.date_utils import next_month, parse_iso_date
from data.db import db
from services.boost_day_service import add_proposal, get_user_proposals, get_month_proposals


load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class ChunithmBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(command_prefix="/", intents=intents)

    async def setup_hook(self) -> None:
        # Initialize database on startup.
        db.init_db()
        # Sync application (slash) commands on startup.
        await self.tree.sync()


bot = ChunithmBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} - {bot.user.id}")


@bot.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}!")


CUT_OFF_DAY = 15  # Mid-month cutoff for current-month proposals.


@bot.tree.command(name="boostday", description="Propose a date for the boost day (YYYY-MM-DD)")
@app_commands.describe(target_date="Date in YYYY-MM-DD format")
async def boost_day_propose(interaction: discord.Interaction, target_date: str):
    today = date.today()
    parsed = parse_iso_date(target_date)

    if parsed is None:
        await interaction.response.send_message(
            "Invalid date format. Please use YYYY-MM-DD.", ephemeral=True
        )
        return

    if parsed < today:
        await interaction.response.send_message(
            "That date is in the past. Please choose a future date.", ephemeral=True
        )
        return

    current_month_key = (today.year, today.month)
    next_m = next_month(today)
    next_month_key = (next_m.year, next_m.month)
    target_key = (parsed.year, parsed.month)

    if target_key not in (current_month_key, next_month_key):
        await interaction.response.send_message(
            "Please propose a date in the current or next month.", ephemeral=True
        )
        return

    if today.day > CUT_OFF_DAY and target_key == current_month_key:
        await interaction.response.send_message(
            "Registrations for this month are closed after the cutoff. Please propose a date for next month.",
            ephemeral=True,
        )
        return

    # Persist the proposal (allows multiple per user per month, but no duplicate date per user/month)
    month_key = f"{parsed.year:04d}-{parsed.month:02d}"
    try:
        add_proposal(interaction.user.id, parsed, month_key)
        await interaction.response.send_message(
            f"✅ Saved your proposal for **{parsed.isoformat()}**.",
            ephemeral=True,
        )
    except sqlite3.IntegrityError:
        await interaction.response.send_message(
            "⚠️ You already proposed that date for this month.",
            ephemeral=True,
        )
    except Exception as e:
        logging.error(f"Failed to save proposal for user {interaction.user.id}: {e}")
        await interaction.response.send_message(
            "❌ Failed to save your proposal. Please try again later.",
            ephemeral=True,
        )


@bot.tree.command(name="my_boost_proposals", description="View all your boost day proposals for a month")
@app_commands.describe(month="Month in YYYY-MM format (default: current month)")
async def my_boost_proposals(interaction: discord.Interaction, month: str = None):
    today = date.today()
    
    # Use provided month or default to current month
    if month is None:
        month_key = f"{today.year:04d}-{today.month:02d}"
    else:
        month_key = month
    
    try:
        proposals = get_user_proposals(interaction.user.id, month_key)
        
        if not proposals:
            await interaction.response.send_message(
                f"No proposal found for {month_key}. Use `/boostday` to create one.",
                ephemeral=True,
            )
        else:
            proposal_list = "\n".join([
                f"• **{p.target_date.isoformat()}** (submitted {p.created_at.strftime('%Y-%m-%d %H:%M:%S')})"
                for p in proposals
            ])
            embed = discord.Embed(
                title="Your Boost Day Proposals",
                color=discord.Color.blue()
            )
            embed.add_field(name="Month", value=month_key, inline=False)
            embed.add_field(name="Proposals", value=proposal_list, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        logging.error(f"Failed to fetch proposal for user {interaction.user.id}: {e}")
        await interaction.response.send_message(
            "❌ Failed to retrieve your proposal. Please try again later.",
            ephemeral=True,
        )


@bot.tree.command(name="boost_proposals", description="View all proposals for a month")
@app_commands.describe(month="Month in YYYY-MM format (default: current month)")
async def boost_proposals(interaction: discord.Interaction, month: str = None):
    today = date.today()
    
    # Use provided month or default to current month
    if month is None:
        month_key = f"{today.year:04d}-{today.month:02d}"
    else:
        month_key = month
    
    try:
        proposals = get_month_proposals(month_key)
        
        if not proposals:
            await interaction.response.send_message(
                f"No proposals found for {month_key}.",
                ephemeral=True,
            )
        else:
            # Build a list of all proposals
            proposal_list = "\n".join([
                f"• **{p.target_date.isoformat()}** (User: {p.user_id})"
                for p in proposals
            ])
            
            embed = discord.Embed(
                title=f"Boost Day Proposals for {month_key}",
                description=proposal_list,
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Total proposals: {len(proposals)}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        logging.error(f"Failed to fetch proposals for month {month_key}: {e}")
        await interaction.response.send_message(
            "❌ Failed to retrieve proposals. Please try again later.",
            ephemeral=True,
        )


bot.run(token, log_handler=handler, log_level=logging.DEBUG)