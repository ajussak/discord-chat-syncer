#!/usr/bin/env python3

import discord
import json

config = json.load(open("config.json"))
client = discord.Client()


@client.event
async def on_message(message):
    if message.author.id != client.user.id and message.channel.id in config["syncedChannels"] \
            and not message.content.startswith("!"):
        for embed in message.embeds:
            message.attachments.append(embed["image"])
        for object in message.attachments:
            if message.content != "":
                message.content += "\n"
            message.content += object["url"]
        for synced_channel_id in config["syncedChannels"]:
            if synced_channel_id != message.channel.id:
                await client.send_message(client.get_channel(synced_channel_id),  message.content)

print("Discord Chat Syncer\n\nBot is running...")
client.run(config["token"])
