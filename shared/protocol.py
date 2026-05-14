API_REGISTER = "/api/register"
API_APPROVE = "/api/approve"
API_PING = "/api/ping"
API_SCAN = "/api/scan"
API_CLIENTS = "/api/clients"
API_CLIENT_DETAIL = "/api/clients/<key>"
API_MANUAL_UPDATE = "/api/clients/<key>/manual"
API_ADDONS = "/api/clients/<key>/addons"
API_ADDON_DELETE = "/api/clients/<key>/addons/<int:addon_id>"
API_SCAN_CONFIG = "/api/clients/<key>/scan-config"
API_TRIGGER_SCAN = "/api/clients/<key>/scan-now"
API_DELETE_CLIENT = "/api/clients/<key>/delete"

KEY_LENGTH = 8
HEARTBEAT_INTERVAL = 30
DEFAULT_SCAN_INTERVAL = 3600
