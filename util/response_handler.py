def get_response_type(guild_id):
    pass

def check_set_response(message):
    message_content = message.content
    return message_content == "channel" or message_content == "dm"
