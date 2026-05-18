import sys
import os
import argparse
import subprocess
import django
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="System Scanner Pro - Admin Panel")
    parser.add_argument("--port", type=int, default=80, help="Server port (default: 80)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--username", type=str, default="admin", help="Default admin username")
    parser.add_argument("--password", type=str, default="admin123", help="Default admin password")
    args = parser.parse_args()

    print("=" * 55)
    print("  System Scanner Pro Admin Panel v2.1")
    print("  (Django + DRF + Bootstrap 5)")
    print("=" * 55)
    print()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_admin.settings")
    os.chdir(Path(__file__).parent)

    manage_py = Path(__file__).parent / "manage.py"

    django.setup()
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
    webbrowser.open(f"http://127.0.0.1:{args.port}")

    cmd = [sys.executable, str(manage_py), "runserver", f"{args.host}:{args.port}"]
    if args.debug:
        cmd.append("--noreload")

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
