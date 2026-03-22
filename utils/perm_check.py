from data.config_store import get_all_role_permissions
import discord

from dotenv import dotenv_values
from utils.permissions import Permission

async def has_admin_like_permission(interaction: discord.Interaction) -> bool:
    """
    Check if the user has permission to manage permissions.
    Allowed if they have Discord's manage_roles permission OR have a role with Permission.ADMIN.
    Must check if user is in a guild first.

    :param interaction: The Discord interaction
    :return: True if the user can manage permissions, False otherwise
    """
    
    if owner := dotenv_values('.env').get('BOT_OWNER'): 
      if owner == str(interaction.user.id):
        return True

    # Check if user is in a guild
    if interaction.channel is None:
        return False

    # Check if user has Discord manage_roles permission
    if interaction.channel.permissions_for(interaction.user).manage_roles:
        return True
    
    # Check if user has any role with Permission.ADMIN in the database
    role_permissions = get_all_role_permissions()
    for role in interaction.user.roles:
        if Permission.check_is_admin(role_permissions.get(role.id, Permission.NONE)):
            return True
        
    return False

async def has_member_permission(interaction: discord.Interaction) -> bool:
    """
    Check if the user has at least member-level permission.
    Allowed if they have Discord's manage_roles permission OR have a role with Permission.MEMBER or higher.
    Must check if user is in a guild first.
    
    :param interaction: The Discord interaction
    :return: True if the user has member permission, False otherwise
    """
    if await has_admin_like_permission(interaction):
        return True  # Admin-like permissions imply member permissions

    # Check if user is in a guild
    if interaction.channel is None:
        return False
    
    # Check if user has any role with Permission.MEMBER or higher in the database
    role_permissions = get_all_role_permissions()
    for role in interaction.user.roles:
        if Permission.check_has(role_permissions.get(role.id, Permission.NONE), Permission.MEMBER):
            return True
    
    return False