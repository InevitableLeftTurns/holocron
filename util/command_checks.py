import discord
from discord.utils import get


async def check_higher_perms(author: discord.Member, guild: discord.Guild):
    bot_perms = get(guild.roles, name="Holocron Admin")

    if author.guild_permissions.administrator or bot_perms in author.roles:
        return True
    return False
