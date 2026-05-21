import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from shared.runtime import is_frozen, get_client_data_dir


def get_admin_url():
    config_path = os.path.join(get_client_data_dir(), "client_config.json")
    defaults = {"admin_url": "http://localhost:80"}
    try:
        if os.path.exists(config_path):
            import json
            with open(config_path) as f:
                data = json.load(f)
                defaults.update(data)
    except Exception:
        pass
    return defaults["admin_url"]


def prompt_admin_url():
    url = input("Enter Admin Server URL (e.g., http://192.168.1.100:80): ").strip()
    if not url:
        url = "http://localhost:80"
    return url.rstrip("/")
