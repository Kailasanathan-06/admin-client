import sys
import os
import time
import json
import threading
from datetime import datetime

from .key_manager import load_or_create_key, load_config, save_config
from .config import get_admin_url, prompt_admin_url
from .communicator import Communicator
from .scanner import collect_all, get_hostname, detect_platform


VERSION = "1.0.0"


def print_header():
    print("=" * 55)
    print(f"  System Scanner Pro Client v{VERSION}")
    print("=" * 55)
    print()


def run_manual_scan(comm, key, hostname):
    print("  Starting manual scan...")
    data = collect_all()
    print("  Sending scan data to admin...")
    result = comm.send_scan(key, hostname, "manual", data)
    if result.get("status") == "ok":
        print("  [OK] Scan data sent successfully.")
    else:
        print(f"  [FAIL] {result.get('message', 'Unknown error')}")
    return data


def run_scheduled_scan(comm, key, hostname, interval):
    while True:
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] Running scheduled scan...")
        data = collect_all()
        result = comm.send_scan(key, hostname, "scheduled", data)
        if result.get("status") == "ok":
            print(f"  [OK] Data sent. Next scan in {interval // 60} minutes.")
        else:
            print(f"  [WARN] {result.get('message', 'Send failed')}. Retrying in 60s...")
            time.sleep(60)
            continue
        time.sleep(interval)


def heartbeat_loop(comm, key, hostname):
    while True:
        try:
            comm.ping(key, hostname)
        except Exception:
            pass
        time.sleep(30)


def main():
    print_header()

    key = load_or_create_key()
    print(f"  Your Registration Key: {key}")
    print()

    config = load_config()
    admin_url = config.get("admin_url", "")

    if not admin_url or admin_url == "http://localhost:80":
        if len(sys.argv) > 1 and sys.argv[1].startswith("http"):
            admin_url = sys.argv[1].rstrip("/")
            config["admin_url"] = admin_url
            save_config(config)
        else:
            print("  First-time setup required.")
            admin_url = prompt_admin_url()
            config["admin_url"] = admin_url
            save_config(config)

    hostname = get_hostname()
    platform_name, _ = detect_platform()
    comm = Communicator(admin_url)

    print(f"  Admin Server: {admin_url}")
    print(f"  Hostname: {hostname}")
    print(f"  Platform: {platform_name}")
    print()

    print("  Connecting to admin server...")
    result = comm.register(key, hostname, platform_name)

    if result.get("status") == "ok":
        print("  [OK] Registered with admin server.")
    elif result.get("status") == "pending":
        print("  [WAITING] Registration key sent. Waiting for admin approval...")
        while True:
            time.sleep(5)
            status_res = comm.check_status(key)
            if status_res.get("status") == "approved":
                print("  [OK] Admin approved registration.")
                break
            elif status_res.get("status") == "error":
                pass
    else:
        print(f"  [WARN] {result.get('message', 'Registration pending')}")

    print()
    print("  Starting heartbeat...")
    hb_thread = threading.Thread(target=heartbeat_loop, args=(comm, key, hostname), daemon=True)
    hb_thread.start()

    mode = config.get("scan_mode", "scheduled")

    parsed = None
    try:
        import argparse
        parser = argparse.ArgumentParser(description="System Scanner Pro Client")
        parser.add_argument("--mode", choices=["manual", "scheduled", "once"], help="Scan mode")
        parser.add_argument("--interval", type=int, help="Scan interval in seconds")
        parser.add_argument("url", nargs="?", help="Admin server URL")
        args, _ = parser.parse_known_args()
        if args.mode:
            mode = args.mode
        if args.interval:
            config["scan_interval"] = args.interval
            save_config(config)
    except Exception:
        pass

    if mode == "manual":
        print("  [MANUAL MODE] Type 'scan' to run a scan, 'exit' to quit.")
        while True:
            try:
                cmd = input("  > ").strip().lower()
                if cmd == "scan":
                    run_manual_scan(comm, key, hostname)
                elif cmd == "exit":
                    break
                elif cmd:
                    print(f"  Unknown command: {cmd}")
            except (EOFError, KeyboardInterrupt):
                break
    elif mode == "once":
        run_manual_scan(comm, key, hostname)
    else:
        interval = config.get("scan_interval", 3600)
        print(f"  [SCHEDULED MODE] Scanning every {interval // 60} minutes.")
        print("  Press Ctrl+C to stop.")
        try:
            run_scheduled_scan(comm, key, hostname, interval)
        except KeyboardInterrupt:
            print("\n  Stopped.")


if __name__ == "__main__":
    main()
