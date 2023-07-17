bot_prefixes = {}


def bot_prefix(bot_instance, message):
    if message.guild is None:
        return bot_prefixes["0"]
    return bot_prefixes.get(str(message.guild.id), bot_prefixes["0"])
