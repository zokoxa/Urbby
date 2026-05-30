import logging
from time import perf_counter
import discord
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

log = logging.getLogger(__name__)

UD_COLOR = 0xFFC107
UD_ICON = "https://www.urbandictionary.com/favicon.ico"
UD_URL = "https://www.urbandictionary.com"
REQUEST_TIMEOUT_SECONDS = 15
WORD_SELECTOR = "a.word, span.word, h2 a"
PARSER_PREVIEW_CHARS = 180


def _clean_text(value):
    if value is None:
        return None
    return value.get_text(" ", strip=True).replace("[", "").replace("]", "").replace("`", "'")


def _fetch_page(url, label):
    started = perf_counter()
    log.info("[HTTP] Fetching %s: %s", label, url)
    try:
        req = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException:
        elapsed_ms = (perf_counter() - started) * 1000
        log.exception("[!!] Urban Dictionary request failed for %s after %.0fms", label, elapsed_ms)
        raise

    elapsed_ms = (perf_counter() - started) * 1000
    content_type = req.headers.get("content-type", "unknown")
    log.info(
        "[HTTP] %s -> %s in %.0fms (%s, %s chars)",
        label,
        req.status_code,
        elapsed_ms,
        content_type,
        len(req.text),
    )

    try:
        req.raise_for_status()
    except requests.HTTPError:
        log.exception("[!!] Urban Dictionary returned HTTP %s for %s", req.status_code, label)
        raise

    return req


def _describe_page(soup):
    title = _clean_text(soup.title) if soup.title else "no title"
    return (
        f"title={title!r}, "
        f"word_matches={len(soup.select(WORD_SELECTOR))}, "
        f"meaning_matches={len(soup.select('div.meaning'))}, "
        f"example_matches={len(soup.select('div.example'))}"
    )


def _log_parse_failure(soup, label, missing):
    preview = soup.get_text(" ", strip=True)[:PARSER_PREVIEW_CHARS]
    log.warning(
        "[!!] Could not parse Urban Dictionary %s; missing %s (%s). Preview: %r",
        label,
        ", ".join(missing),
        _describe_page(soup),
        preview,
    )


def _find_entry_container(soup):
    word_link = soup.select_one(WORD_SELECTOR)
    if not word_link:
        return None

    for parent in word_link.parents:
        if not getattr(parent, "find", None):
            continue
        if parent.find("div", class_="meaning"):
            return parent
    return None


def _extract_entry(soup, label):
    container = _find_entry_container(soup)
    search_root = container or soup

    word_el = search_root.select_one(WORD_SELECTOR)
    definition_el = search_root.select_one("div.meaning")
    example_el = search_root.select_one("div.example")

    if not word_el or not definition_el:
        missing = []
        if not word_el:
            missing.append("word")
        if not definition_el:
            missing.append("definition")
        _log_parse_failure(soup, label, missing)
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
    req = _fetch_page(f"{UD_URL}/", "word of the day")
    soup = BeautifulSoup(req.text, "html.parser")
    entry = _extract_entry(soup, "word of the day")
    if not entry:
        raise ValueError("Could not parse Urban Dictionary word of the day entry")
    word = entry["word"]
    definition = entry["definition"]
    example = entry["example"]
    log.info(f"[OK] Word of the day: '{word}'")
    return {"list": [{"word": word, "definition": definition, "example": example}]}


def define(word) -> discord.Embed | None:
    log.info(f"[>>] Looking up '{word}' on Urban Dictionary")
    req = _fetch_page(f"{UD_URL}/define.php?term={quote(word)}", f"definition '{word}'")
    soup = BeautifulSoup(req.text, "html.parser")
    entry = _extract_entry(soup, f"definition '{word}'")
    if not entry:
        log.warning("[--] No Urban Dictionary entry parsed for '%s'", word)
        return None
    log.info(
        "[OK] Definition parsed for '%s' as '%s' (%s definition chars, %s example chars)",
        word,
        entry["word"],
        len(entry["definition"] or ""),
        len(entry["example"] or ""),
    )
    return build_embed(entry["word"], word, entry["definition"], entry["example"])
