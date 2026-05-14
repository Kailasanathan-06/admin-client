import json
import os
import random
import string
from pathlib import Path


KEY_FILE = "client_key.json"


def generate_key(length=8):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


def load_or_create_key():
    key_path = Path(KEY_FILE)
    if key_path.exists():
        try:
            with open(key_path) as f:
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
    config_path = Path("client_config.json")
    defaults = {
        "admin_url": "http://localhost:80",
        "scan_interval": 3600,
        "auto_start": True,
    }
    if config_path.exists():
        try:
            with open(config_path) as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def save_config(config):
    with open("client_config.json", "w") as f:
        json.dump(config, f, indent=2)
