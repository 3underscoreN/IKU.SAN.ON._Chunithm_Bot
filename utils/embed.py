import discord

from typing import Iterable

def error_embed(title: str = '❌ 錯誤', description: str = '', **kwargs) -> discord.Embed:
    """Create a standardized error embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=kwargs.get('color', discord.Color.red()),
        **kwargs
    )
    return embed

def info_embed(
        title: str = 'ℹ️ 資訊', 
        description: str = '', 
        *,
        color: discord.Color = discord.Color.blue(),
        fields: Iterable[tuple[str, str, bool]] = (),
        **kwargs
        ) -> discord.Embed:
    """
    Create a standardized info embed.
    
    :param title: The title of the embed.
    :param description: The description of the embed. Defaults to `""`.
    :param color: The color of the embed (default: blue).
    :param fields: An iterable of fields to add, each as a tuple (name, value, is_inlie).

    :return: A discord.Embed object.
    :rtype: discord.Embed
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        **kwargs
    )

    for name, value, is_inlie in fields:
        embed.add_field(name=name, value=value, inline=is_inlie)
    return embed

def warning_embed(title: str = '⚠️ 警告', description: str = '', **kwargs) -> discord.Embed:
    """Create a standardized warning embed."""
    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.orange(),
        **kwargs
    )
    return embed