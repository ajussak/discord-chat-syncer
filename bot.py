#!/usr/bin/env python3

import discord
import json
import logging
import os

from discord import Embed

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)


def save_config(config_data):
    with open('config.json', 'w') as outfile:
        json.dump(config_data, outfile, indent=4, sort_keys=True)

if not os.path.exists('config.json'):
    config = {'token': '', 'super_admin_id': '', 'enable_anonymity': False, 'delete_banned_users_messages': True,
              'text_only_messages_filtering': False, 'synced_channels': [], 'banned_users': []}
    save_config(config)
else:
    config = json.load(open("config.json"))

if config['token'] == '':
    logger.critical('Configuration file no completed : Discord token is missing')
    exit(1)

if config['super_admin_id'] == '':
    logger.warning('The Super Admin is not defined in configuration file. Moderation system disabled.')

logger.info("Starting...")
client = discord.Client()


@client.event
async def on_message(message):
    if message.author.id != client.user.id and message.channel.id in config["synced_channels"] \
            and not message.content.startswith("!"):
        if not config["enable_anonymity"]:
            message.content = "**{0}@{1}**\n".format(message.author.name, message.channel.server.name) + message.content
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
                    emb = None
                    if len(message.embeds) >= 1:
                        emb = Embed(**message.embeds[0])
                    print(emb.to_dict())
                    send_message = await client.send_message(channel, message.content, embed=emb)
                    broadcast_list += "\n - {0} (ID:{1}) : Message ID:{2}".format(channel.server.name,
                                                                                  channel.server.id,
                                                                                  send_message.id)
        logger.info("Message ID:%s posted by %s (ID:%s) from server %s (ID:%s) broadcasted to : %s",
                    message.id, message.author.name, message.author.id, message.server.name, message.server.id,
                    broadcast_list)
    elif message.content == '!setsync' and message.author == message.channel.server.owner:
        for channel in message.channel.server.channels:
            if channel.id in config["synced_channels"]:
                config["synced_channels"].remove(channel.id)
        config["synced_channels"].append(channel.id)
        save_config(config)
        await client.send_message(message.channel, "Synchronization enabled here.")

client.run(config["token"])
