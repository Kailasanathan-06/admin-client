import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path


DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "scanner.db"


def get_db():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            registration_key TEXT UNIQUE NOT NULL,
            hostname TEXT DEFAULT '',
            platform TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            last_seen TIMESTAMP,
            approved INTEGER DEFAULT 0,
            purchase_cost REAL,
            purchase_date TEXT,
            vendor_name TEXT,
            vendor_contact TEXT,
            warranty_expiry TEXT,
            notes TEXT,
            scan_interval INTEGER DEFAULT 3600,
            scan_enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
            scan_type TEXT DEFAULT 'scheduled',
            scan_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS addon_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            serial_number TEXT DEFAULT '',
            purchase_cost REAL,
            category TEXT DEFAULT '',
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    conn.close()


# --- Client operations ---

def register_client(key, hostname, platform_name):
    conn = get_db()
    existing = conn.execute("SELECT id FROM clients WHERE registration_key=?", (key,)).fetchone()
    if existing:
        conn.execute(
            "UPDATE clients SET hostname=?, platform=?, status='pending', last_seen=? WHERE registration_key=?",
            (hostname, platform_name, datetime.now().isoformat(), key),
        )
        conn.commit()
        conn.close()
        return {"status": "pending", "message": "Key already registered, waiting for approval"}
    conn.execute(
        "INSERT INTO clients (registration_key, hostname, platform, status, last_seen) VALUES (?, ?, ?, 'pending', ?)",
        (key, hostname, platform_name, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()
    return {"status": "pending", "message": "Registration key sent, waiting for admin approval"}


def approve_client(key):
    conn = get_db()
    result = conn.execute(
        "UPDATE clients SET approved=1, status='online' WHERE registration_key=?",
        (key,),
    )
    conn.commit()
    affected = result.rowcount
    conn.close()
    if affected:
        return {"status": "ok", "message": "Client approved"}
    return {"status": "error", "message": "Client not found"}


def ping_client(key, hostname):
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute(
        "UPDATE clients SET status='online', last_seen=?, hostname=? WHERE registration_key=?",
        (now, hostname, key),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


def mark_offline(key):
    conn = get_db()
    conn.execute("UPDATE clients SET status='offline' WHERE registration_key=?", (key,))
    conn.commit()
    conn.close()


def mark_stale_clients(timeout_seconds=90):
    conn = get_db()
    cutoff = datetime.now().isoformat()
    conn.execute(
        "UPDATE clients SET status='offline' WHERE status='online' AND last_seen < datetime('now', ?)",
        (f"-{timeout_seconds} seconds",),
    )
    conn.commit()
    conn.close()


def get_all_clients():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, registration_key, hostname, platform, status, last_seen, approved, "
        "purchase_cost, vendor_name, notes, created_at FROM clients ORDER BY status DESC, last_seen DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_client(key):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM clients WHERE registration_key=?", (key,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    client = dict(row)

    scans = conn.execute(
        "SELECT * FROM scan_results WHERE client_id=? ORDER BY created_at DESC LIMIT 50",
        (client["id"],),
    ).fetchall()
    client["scans"] = [dict(s) for s in scans]

    addons = conn.execute(
        "SELECT * FROM addon_devices WHERE client_id=? ORDER BY added_at DESC",
        (client["id"],),
    ).fetchall()
    client["addons"] = [dict(a) for a in addons]

    conn.close()
    return client


def delete_client(key):
    conn = get_db()
    conn.execute("DELETE FROM clients WHERE registration_key=?", (key,))
    conn.commit()
    conn.close()
    return {"status": "ok"}


# --- Scan operations ---

def save_scan(key, hostname, scan_type, scan_data):
    conn = get_db()
    client = conn.execute("SELECT id FROM clients WHERE registration_key=?", (key,)).fetchone()
    if not client:
        conn.close()
        return {"status": "error", "message": "Client not found"}
    scan_data["hostname"] = hostname
    conn.execute(
        "INSERT INTO scan_results (client_id, scan_type, scan_data) VALUES (?, ?, ?)",
        (client["id"], scan_type, json.dumps(scan_data)),
    )
    conn.execute(
        "UPDATE clients SET status='online', last_seen=? WHERE id=?",
        (datetime.now().isoformat(), client["id"]),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Scan data saved"}


def get_latest_scan(key):
    conn = get_db()
    client = conn.execute("SELECT id FROM clients WHERE registration_key=?", (key,)).fetchone()
    if not client:
        conn.close()
        return None
    row = conn.execute(
        "SELECT * FROM scan_results WHERE client_id=? ORDER BY created_at DESC LIMIT 1",
        (client["id"],),
    ).fetchone()
    conn.close()
    if row:
        data = dict(row)
        data["scan_data"] = json.loads(data["scan_data"]) if isinstance(data["scan_data"], str) else data["scan_data"]
        return data
    return None


# --- Manual/Addon operations ---

def update_manual(key, data):
    conn = get_db()
    fields = ["purchase_cost", "purchase_date", "vendor_name", "vendor_contact", "warranty_expiry", "notes"]
    updates = {k: data.get(k) for k in fields if k in data}
    if updates:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [key]
        conn.execute(f"UPDATE clients SET {set_clause} WHERE registration_key=?", values)
    conn.commit()
    conn.close()
    return {"status": "ok"}


def add_addon(key, data):
    conn = get_db()
    client = conn.execute("SELECT id FROM clients WHERE registration_key=?", (key,)).fetchone()
    if not client:
        conn.close()
        return {"status": "error", "message": "Client not found"}
    conn.execute(
        "INSERT INTO addon_devices (client_id, name, description, serial_number, purchase_cost, category) VALUES (?, ?, ?, ?, ?, ?)",
        (client["id"], data.get("name", ""), data.get("description", ""), data.get("serial_number", ""),
         data.get("purchase_cost"), data.get("category", "")),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Add-on device added"}


def delete_addon(key, addon_id):
    conn = get_db()
    client = conn.execute("SELECT id FROM clients WHERE registration_key=?", (key,)).fetchone()
    if not client:
        conn.close()
        return {"status": "error", "message": "Client not found"}
    conn.execute("DELETE FROM addon_devices WHERE id=? AND client_id=?", (addon_id, client["id"]))
    conn.commit()
    conn.close()
    return {"status": "ok"}


# --- Scan config operations ---

def update_scan_config(key, data):
    conn = get_db()
    interval = data.get("interval_seconds", 3600)
    enabled = 1 if data.get("enabled", True) else 0
    conn.execute(
        "UPDATE clients SET scan_interval=?, scan_enabled=? WHERE registration_key=?",
        (interval, enabled, key),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


def get_scan_config(key):
    conn = get_db()
    row = conn.execute(
        "SELECT scan_interval, scan_enabled FROM clients WHERE registration_key=?", (key,)
    ).fetchone()
    conn.close()
    if row:
        return {"interval_seconds": row["scan_interval"], "enabled": bool(row["scan_enabled"])}
    return {"interval_seconds": 3600, "enabled": True}
