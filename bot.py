import os
import responses
import discord
from discord.ext import tasks
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = discord.Client(intents=discord.Intents.all())

urbanDURL = "https://www.urbandictionary.com/"

triggerCommand = "#"

channels = {}  # {channel_id: {"time": "HH:MM", "tz": "UTC"}}


@tasks.loop(minutes=1)
async def send_message():
    channels_to_send = [
        cid for cid, cfg in channels.items()
        if datetime.now(ZoneInfo(cfg["tz"])).strftime("%H:%M") == cfg["time"]
    ]

    if not channels_to_send:
        return

    word_of_the_day = responses.get_word_of_day()

    for channel_id in channels_to_send:
        this_channel = client.get_channel(channel_id)
        await this_channel.send(responses.handle_word_of_the_day(word_of_the_day))


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Urban Dictionary"))
    send_message.start()
    print('Urbby Clone Bot is running')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # add channel id
    if message.content.upper() == triggerCommand + "SET":
        channel_id = message.channel.id
        if channel_id in channels:
            await message.channel.send("`Channel Already Registered!`")
            return
        channels[channel_id] = {"time": "09:00", "tz": "UTC"}
        word_of_the_day = responses.get_word_of_day()
        await message.channel.send(responses.handle_word_of_the_day(word_of_the_day))
        await message.channel.send("`Channel Registered! Default time is 09:00 UTC. Use #TIME HH:MM to change it and #TIMEZONE <timezone> to set your timezone (e.g. #TIMEZONE America/Los_Angeles).`")

    # remove channel id
    if message.content.upper() == triggerCommand + "REM":
        channel_id = message.channel.id
        if channel_id not in channels:
            await message.channel.send("`Channel not registered! Use #SET first.`")
            return
        channels.pop(channel_id)
        await message.channel.send("`Channel Removed!`")

    # set time for word of the day
    if message.content.upper().startswith(triggerCommand + "TIME "):
        channel_id = message.channel.id
        if channel_id not in channels:
            await message.channel.send("`Channel not registered! Use #SET first.`")
            return
        time_str = message.content[len(triggerCommand) + len("TIME "):].strip()
        try:
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            await message.channel.send("`Invalid time format. Use HH:MM (e.g. #TIME 08:30)`")
            return
        channels[channel_id]["time"] = time_str
        tz = channels[channel_id]["tz"]
        await message.channel.send(f"`Word of the day will be posted at {time_str} {tz} daily.`")

    # set timezone
    if message.content.upper().startswith(triggerCommand + "TIMEZONE "):
        channel_id = message.channel.id
        if channel_id not in channels:
            await message.channel.send("`Channel not registered! Use #SET first.`")
            return
        tz_str = message.content[len(triggerCommand) + len("TIMEZONE "):].strip()
        try:
            ZoneInfo(tz_str)
        except ZoneInfoNotFoundError:
            await message.channel.send("`Invalid timezone. Use a valid IANA timezone (e.g. America/Los_Angeles, America/New_York, Europe/London).`")
            return
        channels[channel_id]["tz"] = tz_str
        time = channels[channel_id]["time"]
        await message.channel.send(f"`Timezone set to {tz_str}. Word of the day will be posted at {time} {tz_str} daily.`")

    #define word
    commands = ["DEFINE", "WHAT IS "]
    for command in commands:
        if message.content.upper().startswith(triggerCommand + command):
            word = message.content[len(triggerCommand) + len(command):].strip()
            if not word:
                await message.channel.send(f"`Please provide a word. Usage: #{command.strip()} <word>`")
                return
            await message.channel.send(responses.define(responses.get_word(word)))

client.run(token)
