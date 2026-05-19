import sys
import os
import time
import json
import socket
import platform
import threading
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from key_manager import load_or_create_key, load_config, save_config
from config import prompt_admin_url
from communicator import Communicator
from scanner import collect_all

VERSION = "1.0.0"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "client_output"


def print_header():
    print("=" * 55)
    print(f"  System Scanner Pro Client v{VERSION}")
    print("  Runs on this machine and reports to admin server")
    print("=" * 55)
    print()


def save_output(data):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"scan_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def display_summary(data):
    if not data or not isinstance(data, dict):
        print("  No scan data available.")
        return
    scan_data = data.get("scan_data") or {}
    hostname = scan_data.get("hostname", "unknown")
    plat = scan_data.get("platform", "unknown")
    ts = scan_data.get("scan_timestamp", data.get("created_at", "unknown"))
    processor = scan_data.get("processor", {})
    ram = scan_data.get("ram", {})
    storage = scan_data.get("storage", {})
    gpu = scan_data.get("gpu", [])
    os_info = scan_data.get("os_info", {})

    print(f"  Hostname:      {hostname}")
    print(f"  Platform:      {plat}")
    print(f"  Scanned at:    {ts}")
    print(f"  CPU:           {processor.get('model', 'N/A')}")
    print(f"  RAM:           {ram.get('capacity_gb', 'N/A')}")
    print(f"  OS:            {os_info.get('version', 'N/A')}")
    gpus = gpu if isinstance(gpu, list) else []
    print(f"  GPU(s):        {', '.join(g.get('name', '') for g in gpus) or 'N/A'}")
    disks = storage.get("disks", [])
    for d in disks:
        print(f"  Disk:          {d.get('model', 'N/A')} ({d.get('size_gb', '?')} GB)")


def heartbeat_loop(comm, key, hostname):
    consecutive_errors = 0
    while True:
        try:
            resp = comm.ping(key, hostname, VERSION)
            consecutive_errors = 0

            if resp.get("trigger_scan"):
                now = datetime.now().strftime('%H:%M:%S')
                print(f"  [{now}] Admin requested scan. Running...")
                scan_data = collect_all()
                result = comm.submit_scan(key, scan_data)
                if result.get("status") == "ok":
                    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Scan submitted successfully!")
                else:
                    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Scan failed: {result.get('message', 'Unknown')}")
                time.sleep(5)
                continue
        except Exception as e:
            consecutive_errors += 1
            if consecutive_errors <= 3:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Heartbeat error: {e}")
            elif consecutive_errors == 4:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Multiple heartbeat errors — will suppress further errors until reconnected")
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

    hostname = socket.gethostname()
    comm = Communicator(admin_url)

    print(f"  Admin Server:  {admin_url}")
    print(f"  Client Key:    {key}")
    print(f"  Client Version: {VERSION}")
    print()

    if not comm.is_reachable():
        print(f"  [ERROR] Cannot reach admin server at {admin_url}")
        print("  Check the URL and make sure the admin server is running.")
        print("  Edit client_config.json to change the admin URL.")
        input("  Press Enter to exit...")
        return

    print("  Connecting to admin server...")
    result = comm.register(key, hostname, platform.system(), VERSION)

    if result.get("status") in ("ok",):
        if result.get("auto_approved"):
            print("  [OK] Auto-approved by admin server.")
        else:
            print("  [WAITING] Registration sent. Waiting for admin approval...")
            while True:
                time.sleep(5)
                status_res = comm.check_status(key)
                if status_res.get("status") == "approved":
                    print("  [OK] Admin approved registration.")
                    break
                elif status_res.get("status") == "error":
                    pass
    elif result.get("status") == "pending":
        print("  [WAITING] Registration pending admin approval...")
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
    print("  Performing initial scan...")
    initial_data = collect_all()
    init_result = comm.submit_scan(key, initial_data)
    if init_result.get("status") == "ok":
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] Initial scan submitted successfully!")
    else:
        print(f"  [{datetime.now().strftime('%H:%M:%S')}] Initial scan failed: {init_result.get('message', 'Unknown')}")
    print()

    print("  Starting heartbeat loop (every 30 seconds)...")
    print("  Press Ctrl+C to stop.")
    print()

    hb_thread = threading.Thread(target=heartbeat_loop, args=(comm, key, hostname), daemon=True)
    hb_thread.start()

    last_scan = time.time()
    while True:
        try:
            now = datetime.now().strftime('%H:%M:%S')
            config = comm.get_scan_config(key)
            interval = config.get("interval_seconds", 3600)
            enabled = config.get("enabled", True)

            elapsed = time.time() - last_scan
            if enabled and elapsed >= interval:
                print(f"  [{now}] Scheduled scan starting...")
                scan_data = collect_all()
                result = comm.submit_scan(key, scan_data)
                if result.get("status") == "ok":
                    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Scheduled scan submitted!")
                else:
                    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Scan failed: {result.get('message', 'Unknown')}")
                last_scan = time.time()

            result = comm.fetch_latest_scan(key)
            if result and result.get("id"):
                print(f"  [{now}] Scan data received.")
                display_summary(result)
                saved = save_output(result)
                print(f"  Output saved to: {saved}")
            else:
                next_min = max(1, int((interval - elapsed) / 60)) if enabled else 30
                print(f"  [{now}] Waiting... next scan in ~{next_min}m")

        except Exception as e:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        print()

        if enabled:
            next_in = max(1, interval - (time.time() - last_scan))
            time.sleep(min(30, next_in))
        else:
            time.sleep(30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Stopped.")
