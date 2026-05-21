# System Scanner Pro v2.1

A system hardware scanning and IT inventory management tool with a centralized admin web panel and distributed client agents. Clients scan their hardware specs and report to the admin server for centralized monitoring, asset tracking, and configuration.

## Features

- **Hardware Scanning** — CPU, RAM, storage, motherboard, GPU, OS, network, software, peripherals, antivirus (Windows/Linux/macOS)
- **Admin Dashboard** — Real-time client overview with stats, charts, search/filter, bulk actions
- **Client Detail** — System info, manual asset fields (purchase cost, vendor, warranty), add-on devices, network, software, scan config with diff detection
- **Client Management** — Registration with approval workflow, heartbeat monitoring, stale detection, grouping
- **Authentication** — Login-protected admin panel with account page and password change
- **Admin Panel** — User management (create/delete admins), scan change notifications, activity log, database info, client status chart
- **Scan History** — Dedicated page to browse all scans with device details, filtering, and full scan detail modal
- **CSV Export** — One-click export of client inventory
- **Local Scan** — Scan the server machine directly from the admin panel
- **Cross-Platform** — Admin and client run on Windows, Linux, and macOS
- **Portable Executables** — PyInstaller builds for distribution without Python

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.x + Django REST Framework 3.15 |
| Database | SQLite (default) |
| Frontend | Server-rendered Django templates + vanilla JS |
| UI | Bootstrap 5.3 (dark/light themes) + Chart.js |
| Icons | Bootstrap Icons |
| Build | PyInstaller 6.x |

## Quick Start (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the admin server (auto-creates admin user + DB on first run)
python admin/main.py

# Default login: admin / admin123
# Dashboard: http://localhost
```

### Custom port / credentials

```bash
python admin/main.py --port 8080 --debug --username admin --password mypass
python admin/main.py --reset   # Re-prompt for bind address
```

### Management commands

```bash
python admin/manage.py scan_local              # Scan this machine
python admin/manage.py stale_checker           # Run stale client detector
python admin/manage.py migrate                 # Apply DB migrations
```

## Running the Client

```bash
# Install dependencies (none needed — client uses stdlib only)
# Run the client agent (will prompt for admin server URL on first run)
python client/main.py

# Or specify the admin URL directly
python client/main.py http://192.168.1.100:80
```

The client will:
1. Generate a unique registration key (saved to `client_key.json`)
2. Register with the admin server
3. Perform an initial hardware scan
4. Enter a heartbeat loop (pings every 30s, listens for scan triggers)
5. Perform scheduled scans at the configured interval

## Project Structure

```
admin-client/
├── admin/                   # Admin server (Django app)
│   ├── django_admin/        # Django project config (settings, urls)
│   ├── scanner_api/         # DRF app (models, views, serializers)
│   ├── templates/           # HTML templates (7 pages)
│   ├── static/              # CSS / JS assets
│   ├── data/                # SQLite database (created at runtime)
│   ├── main.py              # Entry point
│   └── manage.py            # Django management CLI
├── client/                  # Client agent (runs on scanned machines)
│   ├── main.py              # Client entry point
│   ├── scanner.py           # Hardware scanner (cross-platform)
│   ├── communicator.py      # HTTP client (stdlib urllib only)
│   ├── key_manager.py       # Registration key generation/storage
│   └── config.py            # Admin URL configuration
├── shared/                  # Shared code
│   ├── runtime.py           # Cross-platform data directory helper
│   ├── protocol.py          # API route constants
│   └── schema.py            # Data class definitions
├── build/                   # PyInstaller build specs & scripts
│   ├── admin_client.spec    # Admin executable spec
│   ├── scanner_client.spec  # Client executable spec
│   └── build.py             # Build orchestration script
├── .github/workflows/       # CI/CD workflows
└── requirements.txt
```

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Dashboard | Client overview with stats, charts, search/filter, bulk actions |
| `/login/` | Login | Admin authentication |
| `/logout/` | Logout | End session |
| `/client/<key>/` | Client Detail | Full client info, scan data, manual fields, add-ons, scan config |
| `/settings/` | Settings | Auto-approve, stale threshold, scan interval, groups, system info |
| `/admin-page/` | Admin Panel | User management, scan change notifications, activity log, stats |
| `/account/` | Account | Profile view and password change |
| `/scans/` | Scan History | Browse all scan results with device details and filtering |

## API Endpoints

### Client Registration & Communication
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/register` | Register a client |
| POST | `/api/approve` | Approve a client |
| POST | `/api/ping` | Client heartbeat |
| GET | `/api/clients/<key>/status` | Check approval status |

### Scan Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/scan` | Submit scan data |
| POST | `/api/scan/local` | Scan the admin server |
| POST | `/api/scan/all` | Trigger scan on all clients |
| GET | `/api/scan/history` | List all scans with device info |
| GET | `/api/clients/<key>/scan-results` | Latest scan for a client |
| POST | `/api/clients/<key>/scan-now` | Trigger scan on a client |
| GET/PUT | `/api/clients/<key>/scan-config` | Get/update scan config |

### Client Management
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/clients` | List all clients |
| GET | `/api/clients/<key>` | Client detail + scans + addons |
| DELETE | `/api/clients/<key>` | Delete client |
| PUT | `/api/clients/<key>/manual` | Update manual/asset fields |
| GET/POST | `/api/clients/<key>/addons` | List/add add-on devices |
| DELETE | `/api/clients/<key>/addons/<id>` | Delete add-on device |

### Admin
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/admin/users` | List admin users |
| POST | `/api/admin/users` | Create admin user |
| DELETE | `/api/admin/users/<id>` | Delete admin user |
| GET | `/api/admin/stats` | System statistics |
| GET | `/api/admin/scan-changes` | HW/SW change detections |
| POST | `/api/admin/change-password` | Change own password |

### Other
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/groups` | List client groups |
| POST | `/api/groups` | Create group |
| DELETE | `/api/groups/<id>` | Delete group |
| GET/PUT | `/api/settings` | Global settings |
| GET | `/api/activity-log` | Recent activity |
| GET | `/api/admin-client` | Admin client info |

## Building Executables

### Prerequisites

- Python 3.10+
- PyInstaller 6.x

```bash
pip install pyinstaller
```

### Build for Current Platform

```bash
# Build both admin and client
python build/build.py all

# Build individually
python build/build.py admin
python build/build.py client

# Clean build artifacts
python build/build.py clean
```

### Output

The build produces platform-tagged artifacts in `dist/`:

```
dist/
├── SystemScannerAdmin-win-x64/       # Admin (folder) - Windows
│   └── SystemScannerAdmin.exe
├── SystemScannerClient-win-x64.exe   # Client (single file) - Windows
├── SystemScannerAdmin-linux-x64/     # Admin (folder) - Linux
├── SystemScannerClient-linux-x64     # Client (single file) - Linux
├── SystemScannerAdmin-macos-x64/     # Admin (folder) - macOS
└── SystemScannerClient-macos-x64     # Client (single file) - macOS
```

### Cross-Platform Build with CI

The project includes a GitHub Actions workflow (`.github/workflows/build.yml`) that builds all platforms on release:

```yaml
on:
  release:
    types: [published]
  workflow_dispatch:  # Manual trigger
```

Artifacts are uploaded per platform and attached to releases automatically.

### Runtime Data Directories

When running as a packaged executable, data is stored in the OS-standard user data directory:

| OS | Admin Data Path |
|----|----------------|
| Windows | `%APPDATA%\SystemScannerPro\` |
| Linux | `~/.local/share/SystemScannerPro/` |
| macOS | `~/Library/Application Support/SystemScannerPro/` |

Client data is stored in a `client/` subdirectory. The SQLite database, config files, and keys are all persisted here.

## Running the Packaged Executables

### Admin Server

```cmd
# Windows (double-click or command line)
SystemScannerAdmin.exe

# With options
SystemScannerAdmin.exe --port 8080 --username admin --password mypass
SystemScannerAdmin.exe --reset   # Re-enter bind IP
```

### Client Agent

```cmd
# Windows (double-click or command line)
SystemScannerClient.exe

# With admin URL (or prompted on first run)
SystemScannerClient.exe http://192.168.1.100:80
```

## Scan Data Collected

| Category | Items |
|----------|-------|
| **Processor** | Manufacturer, model, serial, cores, threads, speed, cache |
| **RAM** | Manufacturer, capacity per module, serial, frequency, form factor |
| **Storage** | Disks (model, serial, size, interface), partitions (filesystem, mount) |
| **Motherboard** | Manufacturer, model, serial, BIOS version |
| **GPU** | Name, vendor, dedicated memory |
| **OS** | Name, version, build, architecture, install date |
| **Network** | Interfaces (name, MAC, IPv4, status) |
| **Peripherals** | Keyboards, mice, audio, webcams, printers, USB devices |
| **Software** | Installed applications (name, version, publisher) |
| **Windows Updates** | KB IDs and descriptions (Windows only) |
| **Antivirus** | Antivirus products and firewall status (Windows only) |
| **User Accounts** | Local user accounts |

## Change Detection

The admin panel automatically compares consecutive scans for each client and highlights hardware/software changes:

- **RAM upgrades/downgrades** — capacity, speed changes
- **Storage changes** — new/removed disks, partition changes
- **Software installed/removed** — new applications detected
- **Peripheral connections** — devices added/removed
- **Network changes** — new MAC addresses, IP changes
- **OS updates** — version changes, pending updates

Access change notifications from the **Admin Panel** (`/admin-page/`).

## License

Internal use.
