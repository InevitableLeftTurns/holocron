bot_prefixes = {}


def bot_prefix(bot_instance, message):
    if message.guild is None:
        return bot_prefixes["0"]
    return bot_prefixes.get(str(message.guild.id), bot_prefixes["0"])


def check_prefix_valid(message):
    content = message.content
    return True if len(content) <= 3 and content.find(" ") == -1 else False
