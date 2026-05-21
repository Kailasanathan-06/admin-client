import logging
import socket
import threading
from datetime import datetime
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from .models import Client, ScanResult, AddonDevice, ActivityLog, ClientGroup, Setting
from .diff_utils import compute_scan_diff
from .serializers import (
    ClientListSerializer, ClientDetailSerializer,
    ManualUpdateSerializer, ScanConfigSerializer,
    RegisterRequestSerializer, ApproveRequestSerializer, ApproveMultipleSerializer,
    PingRequestSerializer, ScanSubmitSerializer,
    AddonDeviceSerializer, ActivityLogSerializer,
    ClientGroupSerializer, SettingSerializer,
)

logger = logging.getLogger("scanner_api")


@method_decorator(csrf_exempt, name="dispatch")
class RegisterClientView(APIView):
    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        key = data["registration_key"]
        hostname = data.get("hostname", "")
        platform_name = data.get("platform", "")
        client_version = data.get("client_version", "")

        existing = Client.objects.filter(registration_key=key).first()
        if existing:
            existing.hostname = hostname
            existing.platform = platform_name
            existing.client_version = client_version
            existing.last_seen = timezone.now()
            existing.save(update_fields=["hostname", "platform", "client_version", "last_seen"])
            return Response({"status": "pending", "approved": existing.approved})

        auto_approve = Setting.get("auto_approve", "false").lower() == "true"
        Client.objects.create(
            registration_key=key, hostname=hostname, platform=platform_name,
            client_version=client_version, status="online" if auto_approve else "pending",
            approved=auto_approve, last_seen=timezone.now(),
        )
        ActivityLog.objects.create(action="register", details=f"Client {hostname} registered with key {key}")
        return Response({"status": "ok", "auto_approved": auto_approve}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name="dispatch")
class ApproveClientView(APIView):
    def post(self, request):
        serializer = ApproveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data["registration_key"]

        updated = Client.objects.filter(registration_key=key).update(approved=True, status="online")
        if updated:
            ActivityLog.objects.create(action="approve", details=f"Client with key {key} approved")
            return Response({"status": "ok"})
        return Response({"status": "error", "message": "Client not found"}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name="dispatch")
class ApproveMultipleView(APIView):
    def post(self, request):
        serializer = ApproveMultipleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        keys = serializer.validated_data["registration_keys"]

        count = Client.objects.filter(registration_key__in=keys).update(approved=True, status="online")
        ActivityLog.objects.create(action="approve", details=f"Bulk approved {count} clients")
        return Response({"status": "ok", "count": count})


@method_decorator(csrf_exempt, name="dispatch")
class PingClientView(APIView):
    def post(self, request):
        serializer = PingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        key = data["registration_key"]

        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

        client.status = "online"
        client.last_seen = timezone.now()
        client.hostname = data.get("hostname", client.hostname)
        if data.get("client_version"):
            client.client_version = data["client_version"]

        trigger = client.scan_requested
        if trigger:
            client.scan_requested = False

        client.save(update_fields=["status", "last_seen", "hostname", "client_version", "scan_requested"])

        resp = {"status": "ok"}
        if trigger:
            resp["trigger_scan"] = True
        return Response(resp)


@method_decorator(csrf_exempt, name="dispatch")
class SubmitScanView(APIView):
    def post(self, request):
        serializer = ScanSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        key = data.pop("registration_key")
        hostname = data.pop("hostname", "")
        scan_type = data.pop("scan_type", "scheduled")

        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

        extra = data.pop("_extra", {})
        scan_data = {"hostname": hostname, "scan_type": scan_type, **data, **extra}
        ScanResult.objects.create(client=client, scan_type=scan_type, scan_data=scan_data)

        client.status = "online"
        client.last_seen = timezone.now()
        client.os_version = data.get("os_info", {}).get("version", "")
        client.cpu_model = data.get("processor", {}).get("model", "")
        client.ram_info = data.get("ram", {}).get("capacity_gb", "")
        client.save(update_fields=["status", "last_seen", "os_version", "cpu_model", "ram_info"])

        ActivityLog.objects.create(
            action="scan", client=client,
            details=f"{scan_type} scan from {hostname}"
        )
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class ClientListView(APIView):
    def get(self, request):
        clients = Client.objects.all().select_related("group")
        serializer = ClientListSerializer(clients, many=True)
        return Response(serializer.data)


@method_decorator(csrf_exempt, name="dispatch")
class ClientStatusView(APIView):
    def get(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"status": "approved" if client.approved else "pending", "client_status": client.status})


@method_decorator(csrf_exempt, name="dispatch")
class ClientDetailView(APIView):
    def get(self, request, key):
        try:
            client = Client.objects.prefetch_related("scans", "addons").select_related("group").get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientDetailSerializer(client)
        data = serializer.data

        scans = data.get("scans") or []
        if len(scans) >= 2:
            data["scan_changes"] = compute_scan_diff(scans[1], scans[0])
        else:
            data["scan_changes"] = []
        return Response(data)

    def delete(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
            ActivityLog.objects.create(action="delete", details=f"Deleted client {client.hostname} ({key})")
        except Client.DoesNotExist:
            pass
        Client.objects.filter(registration_key=key).delete()
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class DeleteMultipleView(APIView):
    def post(self, request):
        keys = request.data.get("registration_keys", [])
        count, _ = Client.objects.filter(registration_key__in=keys).delete()
        ActivityLog.objects.create(action="delete", details=f"Bulk deleted {count} clients")
        return Response({"status": "ok", "count": count})


@method_decorator(csrf_exempt, name="dispatch")
class ManualUpdateView(APIView):
    def put(self, request, key):
        serializer = ManualUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = {k: v for k, v in serializer.validated_data.items() if v is not None}

        updated = Client.objects.filter(registration_key=key).update(**data)
        if updated:
            ActivityLog.objects.create(action="update", details=f"Updated fields for client {key}")
            return Response({"status": "ok"})
        return Response({"status": "error", "message": "Client not found"}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name="dispatch")
class AddonListView(APIView):
    def get(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response([])
        return Response(AddonDeviceSerializer(client.addons.all(), many=True).data)

    def post(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = AddonDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(client=client)
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class AddonDeleteView(APIView):
    def delete(self, request, key, addon_id):
        deleted, _ = AddonDevice.objects.filter(id=addon_id, client__registration_key=key).delete()
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class ScanConfigView(APIView):
    def get(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
            return Response({"interval_seconds": client.scan_interval, "enabled": client.scan_enabled})
        except Client.DoesNotExist:
            return Response({"interval_seconds": 3600, "enabled": True})

    def put(self, request, key):
        serializer = ScanConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        updated = Client.objects.filter(registration_key=key).update(
            scan_interval=data["interval_seconds"], scan_enabled=data["enabled"],
        )
        if updated:
            return Response({"status": "ok"})
        return Response({"status": "error", "message": "Client not found"}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name="dispatch")
class TriggerScanView(APIView):
    def post(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Client not found"}, status=status.HTTP_404_NOT_FOUND)

        client.scan_requested = True
        client.save(update_fields=["scan_requested"])
        ActivityLog.objects.create(action="scan_request", client=client, details=f"Scan requested for {client.hostname}")
        return Response({"status": "ok", "message": f"Scan queued for {client.hostname}"})


@method_decorator(csrf_exempt, name="dispatch")
class ScanAllView(APIView):
    def post(self, request):
        count = Client.objects.filter(approved=True).update(scan_requested=True)
        ActivityLog.objects.create(action="scan_request", details=f"Scan requested for {count} clients")
        return Response({"status": "ok", "message": f"Scan queued for {count} client(s)"})


@method_decorator(csrf_exempt, name="dispatch")
class LocalScanView(APIView):
    def post(self, request):
        from .scanner import collect_all, get_hostname, detect_platform

        def run_scan():
            try:
                data = collect_all()
                hostname = get_hostname()
                platform_name, _ = detect_platform()
                scan_data = {"hostname": hostname, "platform": platform_name, "scan_timestamp": datetime.now().isoformat(), "scanned_by": "admin_local", **data}

                admin_key = Setting.get("admin_client_key", "")
                admin_client = Client.objects.filter(registration_key=admin_key).first() if admin_key else None
                ScanResult.objects.create(client=admin_client, scan_type="local", scan_data=scan_data)
                if admin_client:
                    admin_client.status = "online"
                    admin_client.last_seen = timezone.now()
                    admin_client.os_version = data.get("os_info", {}).get("version", "")
                    admin_client.cpu_model = data.get("processor", {}).get("model", "")
                    admin_client.ram_info = data.get("ram", {}).get("capacity_gb", "")
                    admin_client.save(update_fields=["status", "last_seen", "os_version", "cpu_model", "ram_info"])
                logger.info("Admin local scan completed")
            except Exception as e:
                logger.error(f"Admin local scan failed: {e}", exc_info=True)

        threading.Thread(target=run_scan, daemon=True).start()
        return Response({"status": "ok", "message": "Local scan started"})


@method_decorator(csrf_exempt, name="dispatch")
class AdminClientInfoView(APIView):
    def get(self, request):
        key = Setting.get("admin_client_key", "")
        if not key:
            return Response({"registered": False})
        client = Client.objects.filter(registration_key=key).first()
        if not client:
            return Response({"registered": False})
        return Response({"registered": True, "registration_key": client.registration_key, "hostname": client.hostname, "status": client.status})


@method_decorator(csrf_exempt, name="dispatch")
class ClientScanResultsView(APIView):
    def get(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        scan = ScanResult.objects.filter(client=client).order_by("-created_at").first()
        if scan:
            from .serializers import ScanResultSerializer
            return Response(ScanResultSerializer(scan).data)
        return Response(None)


@method_decorator(csrf_exempt, name="dispatch")
class ActivityLogView(APIView):
    def get(self, request):
        limit = int(request.GET.get("limit", 50))
        logs = ActivityLog.objects.select_related("client")[:limit]
        return Response(ActivityLogSerializer(logs, many=True).data)


@method_decorator(csrf_exempt, name="dispatch")
class GroupListView(APIView):
    def get(self, request):
        groups = ClientGroup.objects.all()
        return Response(ClientGroupSerializer(groups, many=True).data)

    def post(self, request):
        name = request.data.get("name", "").strip()
        if not name:
            return Response({"status": "error", "message": "Name required"}, status=status.HTTP_400_BAD_REQUEST)
        group, created = ClientGroup.objects.get_or_create(name=name, defaults={"description": request.data.get("description", "")})
        return Response(ClientGroupSerializer(group).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@method_decorator(csrf_exempt, name="dispatch")
class GroupDeleteView(APIView):
    def delete(self, request, group_id):
        ClientGroup.objects.filter(id=group_id).delete()
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class SettingsView(APIView):
    def get(self, request):
        return Response({
            "auto_approve": Setting.get("auto_approve", "false").lower() == "true",
            "stale_threshold_seconds": int(Setting.get("stale_threshold_seconds", "120")),
            "scan_all_interval": int(Setting.get("scan_all_interval", "86400")),
            "admin_client_key": Setting.get("admin_client_key", ""),
        })

    def put(self, request):
        data = request.data
        if "auto_approve" in data:
            Setting.set("auto_approve", str(data["auto_approve"]).lower())
        if "stale_threshold_seconds" in data:
            Setting.set("stale_threshold_seconds", str(data["stale_threshold_seconds"]))
        if "scan_all_interval" in data:
            Setting.set("scan_all_interval", str(data["scan_all_interval"]))
        ActivityLog.objects.create(action="setting_change", details="Settings updated")
        return Response({"status": "ok"})


@method_decorator(csrf_exempt, name="dispatch")
class AdminUsersView(APIView):
    def get(self, request):
        from django.contrib.auth.models import User
        users = User.objects.all().values("id", "username", "is_superuser", "is_active", "date_joined")
        return Response(list(users))

    def post(self, request):
        from django.contrib.auth.models import User
        username = request.data.get("username", "").strip()
        password = request.data.get("password", "")
        is_superuser = request.data.get("is_superuser", False)
        if not username or not password:
            return Response({"status": "error", "message": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({"status": "error", "message": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password)
        user.is_superuser = is_superuser
        user.save()
        ActivityLog.objects.create(action="login", details=f"Admin user {username} created")
        return Response({"status": "ok", "user": {"id": user.id, "username": user.username, "is_superuser": user.is_superuser}})


@method_decorator(csrf_exempt, name="dispatch")
class AdminUserDeleteView(APIView):
    def delete(self, request, user_id):
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=user_id)
            username = user.username
            user.delete()
            ActivityLog.objects.create(action="delete", details=f"Admin user {username} deleted")
            return Response({"status": "ok"})
        except User.DoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)


@method_decorator(csrf_exempt, name="dispatch")
class AdminStatsView(APIView):
    def get(self, request):
        from django.contrib.auth.models import User
        from .models import Client, ScanResult, ActivityLog
        return Response({
            "total_admins": User.objects.filter(is_superuser=True).count(),
            "total_clients": Client.objects.count(),
            "total_scans": ScanResult.objects.count(),
            "total_logs": ActivityLog.objects.count(),
            "clients_online": Client.objects.filter(approved=True, status__in=["online", "pending"]).count(),
            "clients_pending": Client.objects.filter(approved=False).count(),
            "clients_offline": Client.objects.filter(approved=True, status="offline").count(),
        })


@method_decorator(csrf_exempt, name="dispatch")
class ScanChangesView(APIView):
    def get(self, request):
        from .serializers import ScanResultSerializer
        changes = []
        clients = Client.objects.filter(approved=True, scans__isnull=False).distinct()

        for client in clients:
            scans = ScanResult.objects.filter(client=client).order_by("-created_at")[:2]
            if len(scans) < 2:
                continue
            old_data = scans[1].scan_data or {}
            new_data = scans[0].scan_data or {}
            if old_data == new_data:
                continue
            from .diff_utils import compute_scan_diff
            diffs = compute_scan_diff(
                {"scan_data": old_data},
                {"scan_data": new_data},
            )
            if diffs:
                changes.append({
                    "client_hostname": client.hostname,
                    "client_key": client.registration_key,
                    "client_platform": client.platform,
                    "last_scan": scans[0].created_at.isoformat(),
                    "previous_scan": scans[1].created_at.isoformat(),
                    "change_count": len(diffs),
                    "changes": diffs[:50],
                })

        changes.sort(key=lambda c: c["last_scan"], reverse=True)
        return Response(changes)


@method_decorator(csrf_exempt, name="dispatch")
class ScanHistoryView(APIView):
    def get(self, request):
        query = request.GET.get("q", "").strip().lower()
        scan_type = request.GET.get("type", "").strip().lower()
        limit = int(request.GET.get("limit", 100))

        scans = ScanResult.objects.select_related("client").all().order_by("-created_at")

        if query:
            scans = scans.filter(
                models.Q(client__hostname__icontains=query) |
                models.Q(client__registration_key__icontains=query) |
                models.Q(client__platform__icontains=query)
            )
        if scan_type:
            scans = scans.filter(scan_type=scan_type)

        scans = scans[:limit]
        from .serializers import ScanHistorySerializer
        return Response(ScanHistorySerializer(scans, many=True).data)


@method_decorator(csrf_exempt, name="dispatch")
class ChangePasswordView(APIView):
    def post(self, request):
        from django.contrib.auth.models import User
        user_id = request.data.get("user_id")
        old_password = request.data.get("old_password", "")
        new_password = request.data.get("new_password", "")
        if not user_id or not old_password or not new_password:
            return Response({"status": "error", "message": "All fields required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(new_password) < 4:
            return Response({"status": "error", "message": "Password too short"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        if not user.check_password(old_password):
            return Response({"status": "error", "message": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        ActivityLog.objects.create(action="update", details=f"Password changed for user {user.username}")
        return Response({"status": "ok"})


def get_admin_client_key():
    hostname = socket.gethostname().upper().replace("-", "").replace(".", "")[:12]
    return f"ADMIN-{hostname}"


def ensure_admin_client():
    from .scanner import get_hostname as scan_hostname, detect_platform
    key = get_admin_client_key()
    client, created = Client.objects.get_or_create(
        registration_key=key,
        defaults={"hostname": scan_hostname(), "platform": detect_platform()[0] or "Unknown", "status": "online", "approved": True, "last_seen": timezone.now()},
    )
    Setting.set("admin_client_key", key)
    return key


def admin_self_scan():
    try:
        key = Setting.get("admin_client_key", "")
        if not key:
            return
        admin_client = Client.objects.filter(registration_key=key).first()
        if not admin_client:
            return
        from .scanner import collect_all, get_hostname, detect_platform
        data = collect_all()
        hostname = get_hostname()
        platform_name, _ = detect_platform()
        scan_data = {"hostname": hostname, "platform": platform_name, "scan_timestamp": datetime.now().isoformat(), "scanned_by": "admin_local", **data}
        ScanResult.objects.create(client=admin_client, scan_type="local", scan_data=scan_data)
        admin_client.status = "online"
        admin_client.last_seen = timezone.now()
        admin_client.os_version = data.get("os_info", {}).get("version", "")
        admin_client.cpu_model = data.get("processor", {}).get("model", "")
        admin_client.ram_info = data.get("ram", {}).get("capacity_gb", "")
        admin_client.save(update_fields=["status", "last_seen", "os_version", "cpu_model", "ram_info"])
        logger.info("Admin self-scan completed")
    except Exception as e:
        logger.error(f"Admin self-scan failed: {e}", exc_info=True)
