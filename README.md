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
| `#urbby time HH:MM` | Set the time for the daily word of the day (e.g. `#urbby time 08:30`) |
| `#urbby timezone <tz>` | Set the timezone using IANA format (e.g. `#urbby timezone America/Los_Angeles`) |
| `#urbby define <word>` | Look up a word on Urban Dictionary |
| `#urbby what is <word>` | Look up a word on Urban Dictionary |
| `#urbby help` | Show all available commands |

Commands are case-insensitive.

## Features

- Sends a word of the day every 24 hours to all registered channels
- Looks up any word on Urban Dictionary on demand
- Word of the day is scraped directly from the Urban Dictionary homepage
