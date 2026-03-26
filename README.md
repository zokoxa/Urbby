# Urbby

A Discord bot that fetches word definitions and sends a daily word of the day from Urban Dictionary.

## Setup

1. Clone the repo
2. Install dependencies:
   ```bash
   pip install discord.py requests beautifulsoup4 python-dotenv
   ```
3. Create a `.env` file in the project root:
   ```
   DISCORD_TOKEN=your_token_here
   ```
4. Run the bot:
   ```bash
   python bot.py
   ```

## Commands

| Command | Description |
|---|---|
| `#urbby set` | Register the current channel to receive the daily word of the day (default: 09:00 UTC) |
| `#urbby rm` | Remove the current channel from the daily word list |
| `#urbby time HH:MM` | Set the time for the daily word of the day (e.g. `#urbby time 08:30 AM` or `#urbby time 14:00`) |
| `#urbby timezone <tz>` | Set the timezone using IANA format or common abbreviations (e.g. `PST`, `America/Los_Angeles`) |
| `#urbby define <word>` | Look up a word on Urban Dictionary |
| `#urbby what is <word>` | Look up a word on Urban Dictionary |
| `#urbby help` | Show all available commands |

Commands are case-insensitive.

## Features

- Sends a word of the day to all registered channels at their configured time
- If the word of the day hasn't changed since the last send, the bot will note that it's still the word of the day
- Looks up any word on Urban Dictionary on demand
- If a word isn't found, the bot links directly to the Urban Dictionary submission page
