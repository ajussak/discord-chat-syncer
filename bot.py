#!/usr/bin/env python3

import discord
import json

configfile = open("config.json")
config = json.load(configfile)
client = discord.Client()


@client.event
async def on_message(message):
    if message.author.id != client.user.id and message.channel.id in config["syncedChannels"]:
        for synced_channel_id in config["syncedChannels"]:
            if synced_channel_id != message.channel.id:
                for object in message.attachments:
                    if message.content != "":
                        message.content += "\n"
                    message.content += object["url"]
                await client.send_message(client.get_channel(synced_channel_id),  message.content)

print("Discord Chat Syncer\n\nBot is running...")
client.run(config["token"])
