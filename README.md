# System Scanner Pro v2.0

A system hardware scanning and IT inventory management tool with a centralized admin web panel and distributed client agents. Clients scan their hardware specs and report to the admin server for centralized monitoring, asset tracking, and configuration.

## Features

- **Hardware Scanning** — CPU, RAM, storage, motherboard, GPU, OS, network, software, peripherals (Windows/Linux/macOS)
- **Admin Dashboard** — Real-time client overview with stats, charts, and search/filter
- **Client Detail** — System info, manual asset fields, add-on devices, network, software, scan config
- **Client Management** — Registration with approval workflow, heartbeat monitoring, stale detection
- **Authentication** — Login-protected admin panel with light/dark mode toggle
- **CSV Export** — One-click export of client inventory
- **Local Scan** — Scan the server machine directly from the admin panel

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.x + Django REST Framework 3.15 |
| Database | SQLite (default) / Supabase PostgreSQL |
| Frontend | Server-rendered Django templates + vanilla JS |
| UI | Bootstrap 5.3 (dark/light themes) + Chart.js |
| Icons | Bootstrap Icons |
| Build | PyInstaller (Windows EXE) |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the admin server (auto-creates admin user on first run)
python admin/main.py

# Default login: admin / admin123
# Dashboard: http://localhost
```

### Custom port / credentials
```bash
python admin/main.py --port 8080 --debug --username admin --password mypass
```

### Management commands
```bash
python admin/manage.py scan_local              # Scan this machine
python admin/manage.py stale_checker           # Run stale client detector
python admin/manage.py migrate scanner_api     # Apply DB migrations
```

## Project Structure

```
admin-client/
├── admin/                  # Admin server (Django app)
│   ├── django_admin/       # Django project config
│   ├── scanner_api/        # DRF app (models, views, serializers)
│   ├── templates/          # HTML templates
│   ├── static/             # CSS / JS assets
│   ├── data/               # SQLite database
│   ├── main.py             # Entry point
│   └── manage.py           # Django management CLI
├── client/                 # Client agent (runs on scanned machines)
│   ├── main.py             # Client viewer mode
│   ├── communicator.py     # HTTP client
│   ├── scanner.py          # Hardware scanner (duplicate of admin)
│   └── key_manager.py      # Registration key management
├── shared/                 # Shared code
│   ├── protocol.py         # API route constants
│   └── schema.py           # Data class definitions
├── build/                  # PyInstaller build scripts
└── requirements.txt
```

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/register` | Register a client |
| POST | `/api/approve` | Approve a client |
| POST | `/api/ping` | Client heartbeat |
| POST | `/api/scan` | Submit scan data |
| GET | `/api/clients` | List all clients |
| GET | `/api/clients/<key>` | Client detail + scans + addons |
| DELETE | `/api/clients/<key>` | Delete client |
| PUT | `/api/clients/<key>/manual` | Update manual fields |
| GET/POST | `/api/clients/<key>/addons` | List/add add-on devices |
| GET/PUT | `/api/clients/<key>/scan-config` | Get/update scan config |
| POST | `/api/clients/<key>/scan-now` | Trigger a scan |

## Building EXE

```bash
# Admin panel
build\build_admin.bat

# Client agent
build\build_client.bat
```

## Upgrading

This project was migrated from Flask + raw SQLite to Django + DRF. Legacy files (`server.py`, `database.py`) have been removed. The `scanner.py` module is duplicated between admin and client — future work should extract it into `shared/`.
