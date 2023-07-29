import discord


response_settings = {}


def get_response_type(guild: discord.Guild, user: discord.User, channel: discord.TextChannel):
    setting = response_settings.get(str(guild.id), response_settings["0"])
    if setting == "dm":
        return user
    else:
        return channel

def check_set_response(message: discord.Message):
    message_content = message.content
    return message_content == "channel" or message_content == "dm"

def set_response_method(guild_id_key, method):
    response_settings[guild_id_key] = method
