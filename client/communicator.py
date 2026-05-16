import json
import urllib.request
import urllib.error
import urllib.parse


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

    def register(self, key, hostname, platform_name):
        return self._request("POST", "/api/register", {
            "registration_key": key,
            "hostname": hostname,
            "platform": platform_name,
        })

    def ping(self, key, hostname):
        return self._request("POST", "/api/ping", {
            "registration_key": key,
            "hostname": hostname,
        })

    def fetch_latest_scan(self, key, hostname=None):
        if hostname:
            return self._request("GET", f"/api/clients/{key}/scan-results?hostname={urllib.parse.quote(hostname)}")
        return self._request("GET", f"/api/clients/{key}/scan-results")

    def check_status(self, key):
        return self._request("GET", f"/api/clients/{key}/status")

    def submit_scan(self, key, hostname, scan_data):
        payload = {
            "registration_key": key,
            "hostname": hostname,
            "scan_type": "triggered",
            **scan_data,
        }
        return self._request("POST", "/api/scan", payload, timeout=120)

    def is_reachable(self):
        try:
            result = self._request("GET", "/api/clients", timeout=5)
            return result.get("status") != "error"
        except Exception:
            return False
