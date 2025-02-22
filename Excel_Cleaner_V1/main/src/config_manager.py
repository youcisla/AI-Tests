import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# The config.json is located one level up from the src folder.
CONFIG_FILE = os.path.join(BASE_DIR, "..", "config.json")

def load_config():
    defaults = {
        "allowed_accents": list("àáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞß.\\-'"),
        "allowed_chars_prefix": ["a-zA-Z0-9", "\\s"],
        "replacement_mappings": {"â": "a", "à": "a", "ä": "a", "é": "e", "è": "e", "ë": "e", "ç": "c"},
        "input_folder": os.path.join(BASE_DIR, "..", "input"),
        "output_folder": os.path.join(BASE_DIR, "..", "output")
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            for key in defaults:
                if key not in config:
                    config[key] = defaults[key]
            return config
        except Exception as e:
            print(f"Error reading config file: {e}")
            return defaults
    else:
        return defaults

def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise Exception(f"Error saving config: {e}")
