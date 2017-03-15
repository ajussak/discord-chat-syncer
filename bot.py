#!/usr/bin/env python3

import discord
import json
import logging

config = json.load(open("config.json"))
client = discord.Client()

logger = logging.getLogger("discord-chat-logger")
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("bot.log")
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(fmt='%(asctime)s : %(message)s', datefmt='%d/%m/%Y %H:%M:%S')

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


@client.event
async def on_message(message):
    if message.author.id != client.user.id and message.channel.id in config["synced_channels"] \
            and not message.content.startswith("!"):
        if not config["enable_anonymous"]:
            message.content = "**{0}@{1}**\n".format(message.author.name, message.channel.server.name) + message.content
        for embed in message.embeds:
            message.attachments.append(embed["image"])
        for object in message.attachments:
            if message.content != "":
                message.content += "\n"
            message.content += object["url"]
        broadcast_list = ""
        for synced_channel_id in config["synced_channels"]:
            if synced_channel_id != message.channel.id:
                channel = client.get_channel(synced_channel_id)
                if channel is None:
                    logger.error("Channel ID:%s doesn't exist or the bot is not allowed.", synced_channel_id)
                else:
                    send_message = await client.send_message(channel, message.content)
                    broadcast_list += "\n - {0} (ID:{1}) : Message ID:{2}".format(channel.server.name,
                                                                                  channel.server.id,
                                                                                  send_message.id)

        logger.info("Message ID:%s posted by %s (ID:%s) from server %s (ID:%s) broadcasted to : %s",
                    message.id, message.author.name, message.author.id, message.server.name, message.server.id,
                    broadcast_list)


print("Discord Chat Syncer\n")
client.run(config["token"])
