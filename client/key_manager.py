import sys
import json
import os
import random
import string
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from shared.runtime import is_frozen, get_client_data_dir

CLIENT_DATA_DIR = get_client_data_dir()
KEY_FILE = os.path.join(CLIENT_DATA_DIR, "client_key.json")
CONFIG_FILE = os.path.join(CLIENT_DATA_DIR, "client_config.json")


def generate_key(length=8):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def load_or_create_key():
    if os.path.exists(KEY_FILE):
        try:
            with open(KEY_FILE) as f:
                data = json.load(f)
                return data.get("registration_key")
        except Exception:
            pass
    key = generate_key()
    save_key(key)
    return key


def save_key(key):
    with open(KEY_FILE, "w") as f:
        json.dump({"registration_key": key}, f, indent=2)


def load_config():
    defaults = {
        "admin_url": "http://localhost:80",
        "scan_interval": 3600,
        "auto_start": True,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
