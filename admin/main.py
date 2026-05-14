import sys
import os
import argparse
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="System Scanner Pro - Admin Panel")
    parser.add_argument("--port", type=int, default=80, help="Server port (default: 80)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind address (default: 0.0.0.0)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    print("=" * 55)
    print("  System Scanner Pro Admin Panel v2.0")
    print("  (Django + DRF + Supabase)")
    print("=" * 55)
    print()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_admin.settings")

    manage_py = Path(__file__).parent / "manage.py"

    print(f"  Dashboard: http://{args.host}:{args.port}")
    print()

    import webbrowser
    webbrowser.open(f"http://127.0.0.1:{args.port}")

    cmd = [
        sys.executable, str(manage_py), "runserver",
        f"{args.host}:{args.port}",
    ]
    if args.debug:
        cmd.append("--noreload")

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
