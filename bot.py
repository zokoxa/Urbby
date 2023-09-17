import responses
import discord
from discord.ext import tasks

token = 'MTA4MTI1MTU3NjM1NTc1ODE4MA.G7Z75N.u-McQDY5jIeqK0ja5Yqd3mP719mOOkrWbWV-3A'

client = discord.Client(intents=discord.Intents.all())

urbanDURL = "https://www.urbandictionary.com/"

triggerCommand = "#"

channels = []
# 1081429445300207617


@tasks.loop(hours=24)
async def send_message():

    word_of_the_day = responses.get_word_of_day()

    for channel in channels:
        this_channel = client.get_channel(channel)
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
    if message.content == triggerCommand + "SET":
        channel_id = message.channel.id
        if channels.__contains__(channel_id):
            await message.channel.send("`Channel Already Registered!`")
            return
        channels.append(channel_id)
        word_of_the_day = responses.get_word_of_day()
        await message.channel.send(responses.handle_word_of_the_day(word_of_the_day))
        await message.channel.send("`Channel Registered!`")

    # remove channel id
    if message.content == triggerCommand + "REM":
        channel_id = message.channel.id
        channels.remove(channel_id)
        await message.channel.send("`Channel Removed!`")

    #define word
    commands = ["define ", "what is "]
    for command in commands:
        if message.content.startswith(triggerCommand + command):
            defineWord = message.content[len(triggerCommand) + len(command):]

            await message.channel.send(responses.define(responses.get_word(defineWord)))

client.run(token)
