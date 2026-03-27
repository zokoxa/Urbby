import logging
import discord
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

log = logging.getLogger(__name__)

UD_COLOR = 0xFFC107
UD_ICON = "https://www.urbandictionary.com/favicon.ico"
UD_URL = "https://www.urbandictionary.com"


def build_embed(title, word, definition, example=None) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        url=f"{UD_URL}/define.php?term={quote(word)}",
        description=definition,
        color=UD_COLOR
    )
    if example:
        embed.add_field(name="Example", value=example, inline=False)
    embed.set_footer(text="Urban Dictionary", icon_url=UD_ICON)
    return embed


def handle_word_of_the_day(data) -> discord.Embed:
    first_definition = data["list"][0]
    word = first_definition["word"]
    definition = first_definition["definition"].replace('[', '').replace(']', '')
    example = first_definition.get("example")
    return build_embed(f"Word of the Day: {word}", word, definition, example)


def get_word_of_day():
    log.info("[>>] Fetching word of the day from Urban Dictionary")
    req = requests.get("https://www.urbandictionary.com/")
    soup = BeautifulSoup(req.text, "html.parser")
    word = soup.find("h2").find("a").string
    definition = soup.find("div", class_="break-words meaning mb-4").get_text()
    example_el = soup.find("div", class_="example")
    example = example_el.get_text().strip() if example_el else None
    log.info(f"[OK] Word of the day: '{word}'")
    return {"list": [{"word": word, "definition": definition, "example": example}]}


def define(word) -> discord.Embed | None:
    log.info(f"[>>] Looking up '{word}' on Urban Dictionary")
    req = requests.get(f"{UD_URL}/define.php?term={quote(word)}")
    soup = BeautifulSoup(req.text, "html.parser")
    word_el = soup.find("a", class_="word")
    definition_el = soup.find("div", class_="meaning")
    if not word_el or not definition_el:
        return None
    word_text = word_el.get_text()
    definition_text = definition_el.get_text().replace('`', "'")
    example_el = soup.find("div", class_="example")
    example = example_el.get_text().strip() if example_el else None
    return build_embed(word_text, word, definition_text, example)
