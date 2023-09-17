import requests
from bs4 import BeautifulSoup


def handle_word_of_the_day(data) -> str:
    first_definition = data["list"][0]  # gets first definition
    author = first_definition["author"]  # author of definition
    definition = first_definition["definition"]  # definition of word
    word = first_definition["word"]
    definition = definition.replace('[', '')
    definition = definition.replace(']', '')
    return "`Word of the Day: " + word + " \nDefinition: " + definition + "`"


def get_word_of_day():
    res = requests.get("http://api.urbandictionary.com/v0/define?term=" + scrape_word())
    return res.json()

def get_word(word):
    res = requests.get("http://api.urbandictionary.com/v0/define?term=" + word)
    return res.json()

def define(data):
    first_definition = data["list"][0]  # gets first definition
    author = first_definition["author"]  # author of definition
    definition = first_definition["definition"]  # definition of word
    word = first_definition["word"]
    definition = definition.replace('[', '')
    definition = definition.replace(']', '')
    return "`Word: " + word + " \nDefinition: " + definition + "`"

# scraping from urban dictionary
def scrape_word() -> str:
    req = requests.get("https://www.urbandictionary.com/")
    soup = BeautifulSoup(req.text, "html.parser")
    tag = soup.find('h1')
    word = tag.string
    return word
