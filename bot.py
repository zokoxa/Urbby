import os
import json
import logging
import responses
import discord
from discord.ext import tasks
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

client = discord.Client(intents=discord.Intents.all())

triggerCommand = "#urbby "

CHANNELS_FILE = "channels.json"

pending_timezone = set()  # channel_ids awaiting timezone input
pending_time = set()  # channel_ids awaiting time input


def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, "r") as f:
            data = {int(k): v for k, v in json.load(f).items()}
            log.info(f"[OK] Loaded {len(data)} channel(s) from {CHANNELS_FILE}")
            return data
    log.info("[--] No channels file found, starting fresh")
    return {}


def save_channels():
    with open(CHANNELS_FILE, "w") as f:
        json.dump(channels, f)
    log.info(f"[OK] Saved {len(channels)} channel(s) to {CHANNELS_FILE}")


channels = load_channels()  # {channel_id: {"time": "HH:MM", "tz": "UTC"}}

last_word_sent = None


def fmt_time(time_str):
    """Convert HH:MM to 12-hour AM/PM for display."""
    return datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p").lstrip("0")

def parse_time(time_str):
    """Parse HH:MM or H:MM AM/PM and return 24-hour HH:MM string, or None if invalid."""
    for fmt in ("%I:%M %p", "%I:%M%p", "%H:%M"):
        try:
            return datetime.strptime(time_str.strip(), fmt).strftime("%H:%M")
        except ValueError:
            continue
    return None

TZ_ALIASES = {
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "GMT": "UTC",
    "UTC": "UTC",
}


@tasks.loop(seconds=30)
async def send_message():
    global last_word_sent

    channels_to_send = [
        cid for cid, cfg in channels.items()
        if datetime.now(ZoneInfo(cfg["tz"])).strftime("%H:%M") == cfg["time"]
    ]

    if not channels_to_send:
        return

    log.info(f"[>>] Word of the day triggered for {len(channels_to_send)} channel(s)")
    word_of_the_day = responses.get_word_of_day()
    current_word = word_of_the_day["list"][0]["word"]

    if current_word == last_word_sent:
        log.info(f"[==] '{current_word}' unchanged since last send — using still message")
        message = responses.handle_still_word_of_the_day(word_of_the_day)
    else:
        log.info(f"[>>] New word of the day: '{current_word}'")
        message = responses.handle_word_of_the_day(word_of_the_day)
        last_word_sent = current_word

    for channel_id in channels_to_send:
        this_channel = client.get_channel(channel_id)
        await this_channel.send(embed=message)
        log.info(f"[OK] Sent to channel {channel_id}")


@client.event
async def on_ready():
    await client.change_presence(activity=discord.CustomActivity(name="#urbby define <word>"))
    send_message.start()
    log.info(f"[OK] Urbby bot ready — {len(channels)} registered channel(s)")
    print('Urbby Clone Bot is running')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content
    upper = content.upper()

    # handle pending timezone input
    if message.channel.id in pending_timezone:
        pending_timezone.discard(message.channel.id)
        tz_input = content.strip().upper()
        tz_str = TZ_ALIASES.get(tz_input)
        if not tz_str:
            try:
                ZoneInfo(content.strip())
                tz_str = content.strip()
            except ZoneInfoNotFoundError:
                log.warning(f"[!!] Channel {message.channel.id} — invalid timezone '{content.strip()}', defaulting to UTC")
                await message.channel.send("`Invalid timezone. Defaulting to UTC. Use #urbby timezone <tz> to change it.`")
                tz_str = "UTC"
        channels[message.channel.id]["tz"] = tz_str
        save_channels()
        log.info(f"[OK] Channel {message.channel.id} — timezone set to {tz_str}")
        await message.channel.send(f"`Timezone set to {tz_str}. What time would you like the word of the day? (e.g. 8:30 AM or 14:00)`")
        pending_time.add(message.channel.id)
        return

    # handle pending time input
    if message.channel.id in pending_time:
        pending_time.discard(message.channel.id)
        parsed = parse_time(content)
        if not parsed:
            log.warning(f"[!!] Channel {message.channel.id} — invalid time '{content.strip()}'")
            await message.channel.send("`Invalid time format. Use HH:MM or H:MM AM/PM (e.g. 8:30 AM or 14:00). Time set to default 09:00.`")
            return
        channels[message.channel.id]["time"] = parsed
        save_channels()
        tz = channels[message.channel.id]["tz"]
        log.info(f"[OK] Channel {message.channel.id} — time set to {parsed} {tz}")
        await message.channel.send(f"`Got it! Word of the day will be posted at {fmt_time(parsed)} {tz} daily.`")
        return

    if not upper.startswith(triggerCommand.upper()):
        return

    args = content[len(triggerCommand):].strip()
    args_upper = args.upper()

    # add channel id
    if args_upper == "SET":
        channel_id = message.channel.id
        if channel_id in channels:
            await message.channel.send("`Channel Already Registered!`")
            return
        channels[channel_id] = {"time": "09:00", "tz": "UTC"}
        save_channels()
        log.info(f"[OK] Channel {channel_id} registered")
        await message.channel.send("`Channel Registered! What timezone are you in? (e.g. PST, EST, CST, MST, GMT, UTC)`")
        pending_timezone.add(channel_id)

    # remove channel id
    elif args_upper == "RM":
        channel_id = message.channel.id
        if channel_id not in channels:
            await message.channel.send("`Channel not registered! Use #urbby set first.`")
            return
        channels.pop(channel_id)
        save_channels()
        log.info(f"[--] Channel {channel_id} removed")
        await message.channel.send("`Channel Removed!`")

    # set time for word of the day
    elif args_upper.startswith("TIME "):
        channel_id = message.channel.id
        if channel_id not in channels:
            await message.channel.send("`Channel not registered! Use #urbby set first.`")
            return
        time_str = args[len("TIME "):].strip()
        parsed = parse_time(time_str)
        if not parsed:
            log.warning(f"[!!] Channel {channel_id} — invalid time '{time_str}'")
            await message.channel.send("`Invalid time format. Use HH:MM or H:MM AM/PM (e.g. #urbby time 8:30 AM or #urbby time 14:00)`")
            return
        channels[channel_id]["time"] = parsed
        save_channels()
        tz = channels[channel_id]["tz"]
        log.info(f"[OK] Channel {channel_id} — time updated to {parsed} {tz}")
        await message.channel.send(f"`Word of the day will be posted at {fmt_time(parsed)} {tz} daily.`")

    # set timezone
    elif args_upper.startswith("TIMEZONE "):
        channel_id = message.channel.id
        if channel_id not in channels:
            await message.channel.send("`Channel not registered! Use #urbby set first.`")
            return
        tz_str = args[len("TIMEZONE "):].strip()
        tz_resolved = TZ_ALIASES.get(tz_str.upper())
        if not tz_resolved:
            try:
                ZoneInfo(tz_str)
                tz_resolved = tz_str
            except ZoneInfoNotFoundError:
                log.warning(f"[!!] Channel {channel_id} — invalid timezone '{tz_str}'")
                await message.channel.send("`Invalid timezone. Use PST, EST, CST, MST, GMT, UTC or a valid IANA timezone.`")
                return
        channels[channel_id]["tz"] = tz_resolved
        save_channels()
        time = channels[channel_id]["time"]
        log.info(f"[OK] Channel {channel_id} — timezone updated to {tz_resolved}")
        await message.channel.send(f"`Timezone set to {tz_resolved}. Word of the day will be posted at {fmt_time(time)} {tz_resolved} daily.`")

    # help message
    elif args_upper == "HELP":
        log.info(f"[>>] Help requested in channel {message.channel.id}")
        await message.channel.send(
            "```\n"
            "Urbby Commands\n"
            "──────────────────────────────\n"
            "#urbby set\n"
            "  Register channel for daily word of the day\n"
            "#urbby rm\n"
            "  Unregister channel\n"
            "#urbby time HH:MM\n"
            "  Set daily post time (e.g. 8:30 AM or 14:00)\n"
            "#urbby timezone <tz>\n"
            "  Set timezone (e.g. America/Los_Angeles)\n"
            "#urbby define <word>\n"
            "  Look up a word on Urban Dictionary\n"
            "#urbby what is <word>\n"
            "  Look up a word on Urban Dictionary\n"
            "#urbby help\n"
            "  Show this message\n"
            "```"
        )

    # define word
    elif args_upper.startswith("DEFINE ") or args_upper.startswith("WHAT IS "):
        if args_upper.startswith("DEFINE "):
            word = args[len("DEFINE "):].strip()
        else:
            word = args[len("WHAT IS "):].strip()
        if not word:
            await message.channel.send("`Please provide a word. Usage: #urbby define <word>`")
            return
        log.info(f"[>>] Channel {message.channel.id} — looking up '{word}'")
        result = responses.define(word)
        if result is None:
            log.info(f"[--] '{word}' not found in channel {message.channel.id}")
            await message.channel.send(f"`'{word}' isn't in Urban Dictionary! You can add it here: https://www.urbandictionary.com/add.php`")
        else:
            await message.channel.send(embed=result)

client.run(token)
