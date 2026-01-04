import discord

from typing import Iterable

def error_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized error embed."""
    embed = discord.Embed(
        title = title,
        description = description,
        color = discord.Color.red()
    )
    return embed

def info_embed(
        title: str, 
        description: str = '', 
        *,
        color: discord.Color = discord.Color.blue(),
        fields: Iterable[tuple[str, str, bool]] = ()
        ) -> discord.Embed:
    """
    Create a standardized info embed.
    
    :param title: The title of the embed.
    :param description: The description of the embed. Defaults to `""`.
    :param color: The color of the embed (default: blue).
    :param fields: An iterable of fields to add, each as a tuple (name, value, isInline).

    :return: A discord.Embed object.
    :rtype: discord.Embed
    """
    embed = discord.Embed(
        title = title,
        description = description,
        color = color
    )

    for name, value, isInline in fields:
        embed.add_field(name = name, value = value, inline = isInline)

    return embed