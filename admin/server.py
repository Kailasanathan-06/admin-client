import sys
import os
import json
import threading
import time
import webbrowser
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory

sys.path.insert(0, str(Path(__file__).parent.parent))
from admin.database import (
    init_db, register_client, approve_client, ping_client,
    get_all_clients, get_client, delete_client,
    save_scan, get_latest_scan,
    update_manual, add_addon, delete_addon,
    update_scan_config, get_scan_config, mark_stale_clients,
)

app = Flask(__name__, static_folder="static")


def stale_checker():
    while True:
        time.sleep(30)
        try:
            mark_stale_clients(120)
        except Exception:
            pass


def start_stale_checker():
    t = threading.Thread(target=stale_checker, daemon=True)
    t.start()


# --- API Routes ---

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json()
    key = data.get("registration_key", "")
    hostname = data.get("hostname", "")
    platform_name = data.get("platform", "")
    if not key:
        return jsonify({"status": "error", "message": "No registration key provided"}), 400
    result = register_client(key, hostname, platform_name)
    return jsonify(result)


@app.route("/api/approve", methods=["POST"])
def api_approve():
    data = request.get_json()
    key = data.get("registration_key", "")
    if not key:
        return jsonify({"status": "error", "message": "No key provided"}), 400
    result = approve_client(key)
    return jsonify(result)


@app.route("/api/ping", methods=["POST"])
def api_ping():
    data = request.get_json()
    key = data.get("registration_key", "")
    hostname = data.get("hostname", "")
    if key:
        ping_client(key, hostname)
    return jsonify({"status": "ok"})


@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json()
    key = data.get("registration_key", "")
    hostname = data.get("hostname", "")
    scan_type = data.get("scan_type", "scheduled")
    if not key:
        return jsonify({"status": "error", "message": "No key"}), 400
    result = save_scan(key, hostname, scan_type, data)
    return jsonify(result)


@app.route("/api/clients", methods=["GET"])
def api_clients():
    clients = get_all_clients()
    return jsonify(clients)


@app.route("/api/clients/<key>/status", methods=["GET"])
def api_client_status(key):
    client = get_client(key)
    if not client:
        return jsonify({"status": "error", "message": "Not found"}), 404
    return jsonify({
        "status": "approved" if client.get("approved") else "pending",
        "client_status": client.get("status", "offline"),
    })


@app.route("/api/clients/<key>", methods=["GET"])
def api_client_detail(key):
    client = get_client(key)
    if not client:
        return jsonify({"status": "error", "message": "Not found"}), 404
    scan = get_latest_scan(key)
    return jsonify({"client": client, "latest_scan": scan})


@app.route("/api/clients/<key>", methods=["DELETE"])
def api_delete_client(key):
    result = delete_client(key)
    return jsonify(result)


@app.route("/api/clients/<key>/manual", methods=["PUT"])
def api_manual_update(key):
    data = request.get_json()
    result = update_manual(key, data)
    return jsonify(result)


@app.route("/api/clients/<key>/addons", methods=["GET"])
def api_get_addons(key):
    client = get_client(key)
    if not client:
        return jsonify([])
    return jsonify(client.get("addons", []))


@app.route("/api/clients/<key>/addons", methods=["POST"])
def api_add_addon(key):
    data = request.get_json()
    result = add_addon(key, data)
    return jsonify(result)


@app.route("/api/clients/<key>/addons/<int:addon_id>", methods=["DELETE"])
def api_delete_addon(key, addon_id):
    result = delete_addon(key, addon_id)
    return jsonify(result)


@app.route("/api/clients/<key>/scan-config", methods=["GET", "PUT"])
def api_scan_config(key):
    if request.method == "PUT":
        data = request.get_json()
        result = update_scan_config(key, data)
        return jsonify(result)
    config = get_scan_config(key)
    return jsonify(config)


@app.route("/api/clients/<key>/scan-now", methods=["POST"])
def api_trigger_scan(key):
    return jsonify({"status": "ok", "message": "Scan trigger sent (client will pick up on next ping)"})


# --- Web UI Routes ---

@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/client/<key>")
def client_detail(key):
    return render_template("client_detail.html", client_key=key)


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


def create_app():
    init_db()
    start_stale_checker()
    return app


def run_server(port=80, host="0.0.0.0", debug=False):
    app = create_app()
    print(f"  Admin Server starting on {host}:{port}")
    print(f"  Dashboard: http://127.0.0.1:{port}")
    print()
    webbrowser.open(f"http://127.0.0.1:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False)
