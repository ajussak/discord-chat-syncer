#!/usr/bin/env python3

import json
import logging
import os

import discord
from discord import Embed, ChannelType, Message

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
    config = {'token': '', 'super_admin_id': '', 'enable_anonymity': False, 'text_only_messages_filtering': False,
              'synced_channels': [], 'banned_users': []}
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
        if message.author.id not in config['banned_users'] and (not config['text_only_messages_filtering']
                                                                or not message_is_text_only(message)):
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
                        send_message = await client.send_message(channel, message.content, embed=emb)
                        broadcast_list += "\n - {0} (ID:{1}) : Message ID:{2}".format(channel.server.name,
                                                                                      channel.server.id,
                                                                                      send_message.id)
            logger.info("Message ID:%s posted by %s (ID:%s) from server %s (ID:%s) broadcasted to : %s",
                        message.id, message.author.name, message.author.id, message.server.name, message.server.id,
                        broadcast_list)
        elif message.author.id in config['banned_users'] or (config['text_only_messages_filtering']
                                                             and message_is_text_only(message)):
            try:
                await client.delete_message(message)
            except discord.Forbidden:
                pass

    elif message.channel.type == ChannelType.text and message.content == '!setsync' \
            and message.author == message.channel.server.owner:
        for channel in message.channel.server.channels:
            if channel.id in config["synced_channels"]:
                config["synced_channels"].remove(channel.id)
        config["synced_channels"].append(message.channel.id)
        save_config(config)
        await client.send_message(message.channel, "Synchronization enabled here.")

    elif message.channel.type == ChannelType.private and message.author.id == config['super_admin_id']:
        args = message.content.split(' ')
        if len(args) > 1:
            user_data = get_user(args[1])
            if user_data is not None:
                if args[0] == 'ban':
                    if user_data[0] not in config['banned_users']:
                        config['banned_users'].append(user_data[0])
                        save_config(config)
                        await client.send_message(message.channel, user_data[1] + ' is banned')
                    else:
                        await client.send_message(message.channel, user_data[1] + ' is already banned')
                if args[0] == 'unban':
                    if user_data[0] in config['banned_users']:
                        config['banned_users'].remove(user_data[0])
                        save_config(config)
                        await client.send_message(message.channel, user_data[1] + ' is unbanned')
                    else:
                        await client.send_message(message.channel, user_data[1] + ' is not banned')
        elif message.content == 'banlist':
            msg = 'List of banned users :\n'
            for id in config['banned_users']:
                user = await client.get_user_info(id)
                msg += user.name + '#' + user.discriminator + ' (ID:' + id + ')\n'
            await client.send_message(message.channel, msg)


def get_user(id: str):
    data = id.split('#')

    for member in client.get_all_members():
        if member.id == id:
            return [id, member.name+'#'+member.discriminator]
        elif member.name == data[0] and member.discriminator == data[1]:
            return [member.id, id]
    return None


def message_is_text_only(message: Message) -> bool:
    return not ("http://" in message.content or "https://" in message.content or len(message.embeds) >= 1
                or len(message.attachments) >= 1)

client.run(config["token"])
