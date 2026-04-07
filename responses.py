import logging
import discord
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

log = logging.getLogger(__name__)

UD_COLOR = 0xFFC107
UD_ICON = "https://www.urbandictionary.com/favicon.ico"
UD_URL = "https://www.urbandictionary.com"


def _clean_text(value):
    if value is None:
        return None
    return value.get_text(" ", strip=True).replace("[", "").replace("]", "").replace("`", "'")


def _find_entry_container(soup):
    word_link = soup.select_one("a.word") or soup.select_one("h2 a")
    if not word_link:
        return None

    for parent in word_link.parents:
        if not getattr(parent, "find", None):
            continue
        if parent.find("div", class_="meaning") or parent.find("div", class_="break-words meaning mb-4"):
            return parent
    return None


def _extract_entry(soup):
    container = _find_entry_container(soup)
    search_root = container or soup

    word_el = search_root.select_one("a.word") or search_root.select_one("h2 a")
    definition_el = search_root.select_one("div.break-words.meaning.mb-4") or search_root.select_one("div.meaning")
    example_el = search_root.select_one("div.example")

    if not word_el or not definition_el:
        return None

    return {
        "word": _clean_text(word_el),
        "definition": _clean_text(definition_el),
        "example": _clean_text(example_el),
    }


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
    definition = first_definition["definition"]
    example = first_definition.get("example")
    return build_embed(f"Word of the Day: {word}", word, definition, example)


def get_word_of_day():
    log.info("[>>] Fetching word of the day from Urban Dictionary")
    req = requests.get("https://www.urbandictionary.com/")
    soup = BeautifulSoup(req.text, "html.parser")
    entry = _extract_entry(soup)
    if not entry:
        raise ValueError("Could not parse Urban Dictionary word of the day entry")
    word = entry["word"]
    definition = entry["definition"]
    example = entry["example"]
    log.info(f"[OK] Word of the day: '{word}'")
    return {"list": [{"word": word, "definition": definition, "example": example}]}


def define(word) -> discord.Embed | None:
    log.info(f"[>>] Looking up '{word}' on Urban Dictionary")
    req = requests.get(f"{UD_URL}/define.php?term={quote(word)}")
    soup = BeautifulSoup(req.text, "html.parser")
    entry = _extract_entry(soup)
    if not entry:
        return None
    return build_embed(entry["word"], word, entry["definition"], entry["example"])
