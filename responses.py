import logging
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def handle_word_of_the_day(data) -> str:
    first_definition = data["list"][0]  # gets first definition
    definition = first_definition["definition"]  # definition of word
    word = first_definition["word"]
    definition = definition.replace('[', '')
    definition = definition.replace(']', '')
    return "`Word of the Day: " + word + " \nDefinition: " + definition + "`"


def handle_still_word_of_the_day(data) -> str:
    first_definition = data["list"][0]
    definition = first_definition["definition"]
    word = first_definition["word"]
    definition = definition.replace('[', '')
    definition = definition.replace(']', '')
    return "`Still the Word of the Day: " + word + " \nDefinition: " + definition + "`"


def get_word_of_day():
    log.info("[>>] Fetching word of the day from Urban Dictionary")
    req = requests.get("https://www.urbandictionary.com/")
    soup = BeautifulSoup(req.text, "html.parser")
    word = soup.find("h2").find("a").string
    definition = soup.find("div", class_="break-words meaning mb-4").get_text()
    log.info(f"[OK] Word of the day: '{word}'")
    return {"list": [{"word": word, "definition": definition}]}


def define(word):
    log.info(f"[>>] Looking up '{word}' on Urban Dictionary")
    req = requests.get("https://www.urbandictionary.com/define.php?term=" + word)
    soup = BeautifulSoup(req.text, "html.parser")
    word_el = soup.find("a", class_="word")
    definition_el = soup.find("div", class_="meaning")
    if not word_el or not definition_el:
        return None
    word_text = word_el.get_text()
    definition_text = definition_el.get_text().replace('`', "'")
    return "`Word: " + word_text + " \nDefinition: " + definition_text + "`"

