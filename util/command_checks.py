import discord
from discord.utils import get


async def check_higher_perms(author: discord.Member, guild: discord.Guild):
    bot_perms = get(guild.roles, name="Conquest Admin")
    if bot_perms is None:
        bot_perms = await guild.create_role(name="Conquest Admin")

    if author.guild_permissions.administrator or bot_perms in author.roles:
        return True
    return False
