import sys
import os
import json
import argparse
import django
from pathlib import Path
from django.core.management import call_command

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from shared.runtime import is_frozen, get_app_data_dir, get_resources_dir

DATA_DIR = get_app_data_dir()
RESOURCES_DIR = get_resources_dir()
CONFIG_FILE = os.path.join(DATA_DIR, "admin_config.json")


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="System Scanner Pro - Admin Panel")
    parser.add_argument("--port", type=int, default=80, help="Server port (default: 80)")
    parser.add_argument("--host", type=str, default=None, help="Bind address")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--username", type=str, default="admin", help="Default admin username")
    parser.add_argument("--password", type=str, default="admin123", help="Default admin password")
    parser.add_argument("--reset", action="store_true", help="Re-ask for IP address")
    args = parser.parse_args()

    print("=" * 55)
    print("  System Scanner Pro Admin Panel v2.1")
    print("  (Django + DRF + Bootstrap 5)")
    print("=" * 55)
    print()

    if not args.host:
        saved = load_config()
        if args.reset or not saved.get("host"):
            args.host = input("Enter the IP address to bind (e.g., 0.0.0.0): ").strip()
            if not args.host:
                args.host = "0.0.0.0"
            save_config({"host": args.host})
        else:
            args.host = saved["host"]
            print(f"  Using saved IP: {args.host}")
            print("  (Run with --reset to change IP)")
            print()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_admin.settings")
    os.environ["DJANGO_ALLOWED_HOSTS"] = f"0.0.0.0,127.0.0.1,localhost,{args.host}"
    os.environ["SCANNER_DATA_DIR"] = DATA_DIR
    os.chdir(RESOURCES_DIR)

    django.setup()
    print("  Running database migrations...")
    call_command("migrate", verbosity=0)
    from django.contrib.auth.models import User
    if not User.objects.filter(is_superuser=True).exists():
        User.objects.create_superuser(args.username, "", args.password)
        print(f"  Admin user created: {args.username} / {args.password}")

    from scanner_api.views import ensure_admin_client, admin_self_scan
    admin_key = ensure_admin_client()
    import threading
    threading.Thread(target=admin_self_scan, daemon=True).start()
    print(f"  Admin client key: {admin_key}")
    print()

    print(f"  Dashboard: http://{args.host}:{args.port}")
    print(f"  Login:     http://{args.host}:{args.port}/login/")
    print()

    import webbrowser
    if args.host != "0.0.0.0":
        webbrowser.open(f"http://{args.host}:{args.port}")

    runserver_args = [f"{args.host}:{args.port}"]
    if args.debug:
        runserver_args.append("--noreload")

    call_command("runserver", *runserver_args)


if __name__ == "__main__":
    main()
