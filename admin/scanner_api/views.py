import json
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Client, ScanResult, AddonDevice

from .serializers import (
    ClientListSerializer, ClientDetailSerializer,
    ManualUpdateSerializer, ScanConfigSerializer,
    RegisterRequestSerializer, ApproveRequestSerializer,
    PingRequestSerializer, ScanSubmitSerializer,
    AddonDeviceSerializer,
)


class RegisterClientView(APIView):
    def post(self, request):
        serializer = RegisterRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        key = data["registration_key"]
        hostname = data.get("hostname", "")
        platform_name = data.get("platform", "")

        client, created = Client.objects.update_or_create(
            registration_key=key,
            defaults={
                "hostname": hostname,
                "platform": platform_name,
                "status": "pending",
                "last_seen": timezone.now(),
            },
        )
        if not created:
            return Response({
                "status": "pending",
                "message": "Key already registered, waiting for approval",
            })
        return Response({
            "status": "pending",
            "message": "Registration key sent, waiting for admin approval",
        }, status=status.HTTP_201_CREATED)


class ApproveClientView(APIView):
    def post(self, request):
        serializer = ApproveRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data["registration_key"]

        updated = Client.objects.filter(registration_key=key).update(
            approved=True, status="online"
        )
        if updated:
            return Response({"status": "ok", "message": "Client approved"})
        return Response({"status": "error", "message": "Client not found"},
                        status=status.HTTP_404_NOT_FOUND)


class PingClientView(APIView):
    def post(self, request):
        serializer = PingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        Client.objects.filter(registration_key=data["registration_key"]).update(
            status="online",
            last_seen=timezone.now(),
            hostname=data.get("hostname", ""),
        )
        return Response({"status": "ok"})


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
            return Response({"status": "error", "message": "Client not found"},
                            status=status.HTTP_404_NOT_FOUND)

        scan_data = {
            "registration_key": key,
            "hostname": hostname,
            "scan_type": scan_type,
            **data,
        }
        ScanResult.objects.create(
            client=client, scan_type=scan_type, scan_data=scan_data
        )
        client.status = "online"
        client.last_seen = timezone.now()
        client.save(update_fields=["status", "last_seen"])

        return Response({"status": "ok", "message": "Scan data saved"})


class ClientListView(APIView):
    def get(self, request):
        clients = Client.objects.all()
        serializer = ClientListSerializer(clients, many=True)
        return Response(serializer.data)


class ClientStatusView(APIView):
    def get(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Not found"},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({
            "status": "approved" if client.approved else "pending",
            "client_status": client.status,
        })


class ClientDetailView(APIView):
    def get(self, request, key):
        try:
            client = Client.objects.prefetch_related("scans", "addons").get(
                registration_key=key
            )
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Not found"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = ClientDetailSerializer(client)
        return Response(serializer.data)

    def delete(self, request, key):
        deleted, _ = Client.objects.filter(registration_key=key).delete()
        return Response({"status": "ok"})


class ManualUpdateView(APIView):
    def put(self, request, key):
        serializer = ManualUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = {k: v for k, v in serializer.validated_data.items() if v is not None}

        updated = Client.objects.filter(registration_key=key).update(**data)
        if not updated:
            return Response({"status": "error", "message": "Client not found"},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({"status": "ok"})


class AddonListView(APIView):
    def get(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response([])
        addons = client.addons.all()
        serializer = AddonDeviceSerializer(addons, many=True)
        return Response(serializer.data)

    def post(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"status": "error", "message": "Client not found"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = AddonDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(client=client)
        return Response({"status": "ok", "message": "Add-on device added"})


class AddonDeleteView(APIView):
    def delete(self, request, key, addon_id):
        deleted, _ = AddonDevice.objects.filter(
            id=addon_id, client__registration_key=key
        ).delete()
        return Response({"status": "ok"})


class ScanConfigView(APIView):
    def get(self, request, key):
        try:
            client = Client.objects.get(registration_key=key)
        except Client.DoesNotExist:
            return Response({"interval_seconds": 3600, "enabled": True})
        return Response({
            "interval_seconds": client.scan_interval,
            "enabled": client.scan_enabled,
        })

    def put(self, request, key):
        serializer = ScanConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        updated = Client.objects.filter(registration_key=key).update(
            scan_interval=data["interval_seconds"],
            scan_enabled=data["enabled"],
        )
        if not updated:
            return Response({"status": "error", "message": "Client not found"},
                            status=status.HTTP_404_NOT_FOUND)
        return Response({"status": "ok"})


class TriggerScanView(APIView):
    def post(self, request, key):
        return Response({
            "status": "ok",
            "message": "Scan trigger sent (client will pick up on next ping)",
        })
