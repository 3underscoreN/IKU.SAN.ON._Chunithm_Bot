import discord
from discord import app_commands
from discord.ext import commands

from data.config_store import get_role_permission, set_role_permission, delete_role_permission, get_all_role_permissions
from utils.permissions import Permission
from utils.embed import error_embed, info_embed, warning_embed

from utils.permissions import PermissionMapping
from utils.perm_check import has_admin_like_permission

import logging

logger = logging.getLogger(__name__)

async def permission_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[int]]:
    """
    Autocomplete function for permission levels.
    
    :param interaction: The Discord interaction
    :param current: The current input string
    :return: A list of app_commands.Choice for autocomplete
    """
    choices = []
    for perm_id, perm_name in PermissionMapping.items():
        if perm_id == Permission.NONE:
            continue  # Skip NONE permission in autocomplete
        if current in perm_name:
            choices.append(app_commands.Choice(name=perm_name, value=perm_id))
    return choices

@app_commands.guild_only
@app_commands.check(has_admin_like_permission)
class PermissionsCog(commands.GroupCog, name='permissions'):
    """Manage role-based permissions for the bot."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global error handler for app commands in this cog."""
        logger.error(f"Error in permissions cog: {error}", exc_info=error)

        if isinstance(error, app_commands.NoPrivateMessage):
            embed = error_embed(description='此指令只能在伺服器中使用。')
        else:
            embed = error_embed(description='發生未預期的錯誤，請稍後再試。')
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.edit_original_response(embed=embed, view=None)
    
    @app_commands.command(name='set', description='為一個 Discord 身分組設定權限。')
    @app_commands.describe(
        role='要設定權限的 Discord 身分組',
        permission_level='欲設定的權限等級'
    )
    @app_commands.autocomplete(permission_level=permission_autocomplete)
    @app_commands.check(has_admin_like_permission)
    async def add_permission(self, interaction: discord.Interaction, role: discord.Role, permission_level: int):
        """Add a permission to a role."""

        # Validate permission level
        if permission_level not in (Permission.MEMBER, Permission.ADMIN):
            embed = error_embed(
                description=f"無效的權限等級：{permission_level}。"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Set the permission
        set_role_permission(role.id, permission_level)
        
        perm_name = PermissionMapping[permission_level]
        embed = info_embed(
            title='✅ 權限已新增',
            description=f"已將 {role.mention} 設定為 **{perm_name}**。"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"User {interaction.user} added {perm_name} permission to role {role.id}")
    
    @app_commands.command(name='remove', description='移除 Discord 身分組的權限。')
    @app_commands.describe(role='要移除權限的 Discord 身分組')
    async def remove_permission(self, interaction: discord.Interaction, role: discord.Role):
        """Remove a permission from a role."""

        # Check if role has a permission first
        existing_perm = get_role_permission(role.id)
        if existing_perm is None:
            embed = warning_embed(
                description=f"{role.mention} 目前沒有設定任何權限。"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Remove the permission
        delete_role_permission(role.id)
        
        embed = info_embed(
            title='✅ 權限已移除',
            description=f"已移除 {role.mention} 的所有權限設定。"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"User {interaction.user} removed permissions from role {role.id}")
    
    @app_commands.command(name='view', description='查看所有身分組的權限設定。')
    @app_commands.check(has_admin_like_permission)
    async def view_permissions(self, interaction: discord.Interaction):
        """View all configured role permissions."""

        if interaction.guild is None:
            embed = error_embed(description='此指令只能在伺服器中使用。')
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        role_permissions = get_all_role_permissions()
        
        if not role_permissions:
            embed = info_embed(
                title='身分組權限',
                description='目前沒有任何身分組權限設定。'
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Build permission list
        permissions_list = []
        for role_id, perm_id in sorted(role_permissions.items()):
            try:
                role = await interaction.guild.fetch_role(role_id)
                perm_name = PermissionMapping.get(perm_id, f"未知權限({perm_id})")
                permissions_list.append(f"{role.mention} → **{perm_name}**")
            except discord.NotFound:
                # Role no longer exists, but still show the mapping
                perm_name = PermissionMapping.get(perm_id, f"未知權限({perm_id})")
                permissions_list.append(f"未知身分組 → **{perm_name}**")
        
        embed = info_embed(
            title='身分組權限',
            description='\n'.join(permissions_list) if permissions_list else '目前沒有任何身分組權限設定。'
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def add(bot: commands.Bot):
    """Add the permissions cog to the bot."""
    cog = PermissionsCog(bot)
    await bot.add_cog(cog)
