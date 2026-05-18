import json
import urllib.request
import urllib.error


class Communicator:
    def __init__(self, admin_url):
        self.admin_url = admin_url.rstrip("/")

    def _request(self, method, path, data=None, timeout=30):
        url = f"{self.admin_url}{path}"
        headers = {"Content-Type": "application/json", "User-Agent": "SystemScannerClient/1.0"}
        body = json.dumps(data).encode("utf-8") if data else None
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_data = resp.read().decode("utf-8")
                if resp_data:
                    return json.loads(resp_data)
                return {"status": "ok"}
        except urllib.error.HTTPError as e:
            try:
                err_data = e.read().decode("utf-8")
                return json.loads(err_data)
            except Exception:
                return {"status": "error", "message": f"HTTP {e.code}"}
        except urllib.error.URLError as e:
            return {"status": "error", "message": f"Connection failed: {e.reason}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def register(self, key, hostname, platform_name, client_version=""):
        return self._request("POST", "/api/register", {
            "registration_key": key,
            "hostname": hostname,
            "platform": platform_name,
            "client_version": client_version,
        })

    def ping(self, key, hostname, client_version=""):
        return self._request("POST", "/api/ping", {
            "registration_key": key,
            "hostname": hostname,
            "client_version": client_version,
        })

    def fetch_latest_scan(self, key):
        return self._request("GET", f"/api/clients/{key}/scan-results")

    def check_status(self, key):
        return self._request("GET", f"/api/clients/{key}/status")

    def submit_scan(self, key, scan_data):
        payload = {"registration_key": key, "scan_type": "scheduled", **scan_data}
        return self._request("POST", "/api/scan", payload, timeout=120)

    def get_scan_config(self, key):
        return self._request("GET", f"/api/clients/{key}/scan-config")

    def is_reachable(self):
        try:
            import urllib.request
            import urllib.error
            url = f"{self.admin_url}/api/clients"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5):
                return True
        except Exception:
            return False
