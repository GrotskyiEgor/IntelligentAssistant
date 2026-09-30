import json
import os


with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "themes.json"), "r", encoding="utf-8") as file:
    COLOR_SETTINGS = json.load(file)


def get_theme_colors(settings):
    theme = COLOR_SETTINGS["themes"].get(settings.get("theme", "dark"), COLOR_SETTINGS["themes"]["dark"])
    accent = COLOR_SETTINGS["accents"].get(settings.get("accent", "purple"), COLOR_SETTINGS["accents"]["purple"])
    return theme, accent
