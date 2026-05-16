from rest_framework import serializers
from .models import Client, ScanResult, AddonDevice, Setting


class AddonDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonDevice
        fields = "__all__"


class ScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanResult
        fields = "__all__"
        extra_kwargs = {"scan_data": {"read_only": False}}


class ClientListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = [
            "id", "registration_key", "hostname", "platform",
            "status", "last_seen", "approved", "created_at",
            "purchase_cost", "vendor_name", "notes",
        ]


class ClientDetailSerializer(serializers.ModelSerializer):
    scans = ScanResultSerializer(many=True, read_only=True)
    addons = AddonDeviceSerializer(many=True, read_only=True)

    class Meta:
        model = Client
        fields = "__all__"


class ManualUpdateSerializer(serializers.Serializer):
    hostname = serializers.CharField(required=False, allow_blank=True)
    purchase_cost = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    purchase_date = serializers.DateField(required=False, allow_null=True)
    vendor_name = serializers.CharField(required=False, allow_blank=True)
    vendor_contact = serializers.CharField(required=False, allow_blank=True)
    warranty_expiry = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class ScanConfigSerializer(serializers.Serializer):
    interval_seconds = serializers.IntegerField(default=3600)
    enabled = serializers.BooleanField(default=True)


class RegisterRequestSerializer(serializers.Serializer):
    registration_key = serializers.CharField()
    hostname = serializers.CharField(required=False, default="")
    platform = serializers.CharField(required=False, default="")


class ApproveRequestSerializer(serializers.Serializer):
    registration_key = serializers.CharField()


class PingRequestSerializer(serializers.Serializer):
    registration_key = serializers.CharField()
    hostname = serializers.CharField(required=False, default="")


class ScanSubmitSerializer(serializers.Serializer):
    registration_key = serializers.CharField()
    hostname = serializers.CharField(required=False, default="")
    scan_type = serializers.CharField(required=False, default="scheduled")
    processor = serializers.JSONField(required=False, default=dict)
    ram = serializers.JSONField(required=False, default=dict)
    storage = serializers.JSONField(required=False, default=dict)
    partitions = serializers.ListField(required=False, default=list)
    gpu = serializers.ListField(required=False, default=list)
    motherboard = serializers.JSONField(required=False, default=dict)
    os_info = serializers.JSONField(required=False, default=dict)
    accounts = serializers.ListField(required=False, default=list)
    network = serializers.JSONField(required=False, default=dict)
    peripherals = serializers.JSONField(required=False, default=dict)
    software = serializers.ListField(required=False, default=list)
    updates = serializers.ListField(required=False, default=list)
    monitor = serializers.JSONField(required=False, default=dict)
    antivirus = serializers.JSONField(required=False, default=dict)
    raw_json = serializers.CharField(required=False, default="")


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = "__all__"
