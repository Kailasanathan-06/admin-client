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
from config import get_admin_url, prompt_admin_url
from communicator import Communicator
from scanner import collect_all

VERSION = "1.0.0"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "client_output"


def print_header():
    print("=" * 55)
    print(f"  System Scanner Pro Client v{VERSION}")
    print("  (Viewer Mode — displays scan results from admin)")
    print("=" * 55)
    print()


def save_output(data):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = OUTPUT_DIR / f"scan_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  [SAVED] {path}")
    return path


def display_summary(data):
    if not data or not isinstance(data, dict):
        print("  No scan data available.")
        return
    scan_data = data.get("scan_data") or {}
    hostname = scan_data.get("hostname", "unknown")
    platform = scan_data.get("platform", "unknown")
    ts = scan_data.get("scan_timestamp", data.get("created_at", "unknown"))
    processor = scan_data.get("processor", {})
    ram = scan_data.get("ram", {})
    storage = scan_data.get("storage", {})
    gpu = scan_data.get("gpu", [])
    os_info = scan_data.get("os_info", {})

    print(f"  Hostname:      {hostname}")
    print(f"  Platform:      {platform}")
    print(f"  Scanned at:    {ts}")
    print(f"  CPU:           {processor.get('model', 'N/A')}")
    print(f"  RAM:           {ram.get('capacity_gb', 'N/A')}")
    print(f"  OS:            {os_info.get('version', 'N/A')}")
    print(f"  GPU(s):        {', '.join(g.get('name', '') for g in (gpu if isinstance(gpu, list) else [])) or 'N/A'}")
    disks = storage.get("disks", [])
    if disks:
        for d in disks:
            print(f"  Disk:          {d.get('model', 'N/A')} ({d.get('size_gb', '?')} GB)")


def heartbeat_loop(comm, key, hostname):
    while True:
        try:
            resp = comm.ping(key, hostname)
            if resp.get("trigger_scan"):
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Scan requested by admin. Running scan on this machine...")
                scan_data = collect_all()
                result = comm.submit_scan(key, scan_data)
                if result.get("status") == "ok":
                    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Scan data submitted successfully!")
                else:
                    print(f"  [{datetime.now().strftime('%H:%M:%S')}] Scan submission failed: {result.get('message', 'Unknown')}")
        except Exception as e:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Heartbeat error: {e}")
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
    print()

    print("  Connecting to admin server...")
    result = comm.register(key, hostname, platform.system())

    if result.get("status") == "ok":
        print("  [OK] Registered with admin server.")
    elif result.get("status") == "pending":
        print("  [WAITING] Registration sent. Waiting for admin approval...")
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

    print("  [VIEWER MODE] Fetching latest scan results every 30 seconds.")
    print("  Press Ctrl+C to stop.")
    print()

    while True:
        try:
            result = comm.fetch_latest_scan(key)
            if result and result.get("id"):
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] Latest scan received.")
                display_summary(result)
                saved = save_output(result)
                print(f"  Output saved to: {saved}")
            else:
                print(f"  [{datetime.now().strftime('%H:%M:%S')}] No scan results yet.")
        except Exception as e:
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        print()
        time.sleep(30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Stopped.")
