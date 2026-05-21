from rest_framework import serializers
from .models import Client, ScanResult, AddonDevice, ActivityLog, ClientGroup, Setting


class ClientGroupSerializer(serializers.ModelSerializer):
    client_count = serializers.SerializerMethodField()

    class Meta:
        model = ClientGroup
        fields = ["id", "name", "description", "client_count", "created_at"]

    def get_client_count(self, obj):
        return obj.clients.count()


class ScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScanResult
        fields = ["id", "scan_type", "scan_data", "created_at"]


class ScanHistorySerializer(serializers.ModelSerializer):
    client_hostname = serializers.CharField(source="client.hostname", read_only=True, default="")
    client_key = serializers.CharField(source="client.registration_key", read_only=True, default="")
    client_platform = serializers.CharField(source="client.platform", read_only=True, default="")

    class Meta:
        model = ScanResult
        fields = ["id", "scan_type", "scan_data", "created_at", "client_hostname", "client_key", "client_platform"]


class AddonDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddonDevice
        fields = "__all__"


class ActivityLogSerializer(serializers.ModelSerializer):
    client_hostname = serializers.CharField(source="client.hostname", read_only=True, default="")

    class Meta:
        model = ActivityLog
        fields = ["id", "action", "client_hostname", "details", "created_at"]


class ClientListSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source="group.name", read_only=True, default=None)
    tags_list = serializers.ListField(child=serializers.CharField(), source="tag_list", read_only=True)
    is_stale = serializers.BooleanField(read_only=True)

    class Meta:
        model = Client
        fields = [
            "id", "registration_key", "hostname", "platform", "status",
            "last_seen", "approved", "group", "group_name", "tags_list",
            "is_stale", "client_version", "cpu_model", "ram_info",
            "purchase_cost", "vendor_name", "notes", "created_at",
        ]


class ClientDetailSerializer(serializers.ModelSerializer):
    scans = ScanResultSerializer(many=True, read_only=True)
    addons = AddonDeviceSerializer(many=True, read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True, default=None)
    tags_list = serializers.ListField(child=serializers.CharField(), source="tag_list", read_only=True)
    is_stale = serializers.BooleanField(read_only=True)

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
    group = serializers.PrimaryKeyRelatedField(queryset=ClientGroup.objects.all(), required=False, allow_null=True)
    tags = serializers.CharField(required=False, allow_blank=True)


class ScanConfigSerializer(serializers.Serializer):
    interval_seconds = serializers.IntegerField(min_value=60, max_value=604800, default=3600)
    enabled = serializers.BooleanField(default=True)


class RegisterRequestSerializer(serializers.Serializer):
    registration_key = serializers.CharField()
    hostname = serializers.CharField(required=False, default="")
    platform = serializers.CharField(required=False, default="")
    client_version = serializers.CharField(required=False, default="")


class ApproveRequestSerializer(serializers.Serializer):
    registration_key = serializers.CharField()


class ApproveMultipleSerializer(serializers.Serializer):
    registration_keys = serializers.ListField(child=serializers.CharField())


class PingRequestSerializer(serializers.Serializer):
    registration_key = serializers.CharField()
    hostname = serializers.CharField(required=False, default="")
    client_version = serializers.CharField(required=False, default="")


class ScanSubmitSerializer(serializers.Serializer):
    registration_key = serializers.CharField()
    hostname = serializers.CharField(required=False, default="")
    scan_type = serializers.CharField(required=False, default="scheduled")
    platform = serializers.CharField(required=False, default="")
    platform_version = serializers.CharField(required=False, default="")
    scan_timestamp = serializers.CharField(required=False, default="")
    scanned_by = serializers.CharField(required=False, default="")
    processor = serializers.JSONField(required=False, default=dict)
    ram = serializers.JSONField(required=False, default=dict)
    storage = serializers.JSONField(required=False, default=dict)
    gpu = serializers.ListField(required=False, default=list)
    motherboard = serializers.JSONField(required=False, default=dict)
    os_info = serializers.JSONField(required=False, default=dict)
    accounts = serializers.ListField(required=False, default=list)
    network = serializers.JSONField(required=False, default=dict)
    peripherals = serializers.JSONField(required=False, default=dict)
    software = serializers.ListField(required=False, default=list)
    updates = serializers.ListField(required=False, default=list)
    antivirus = serializers.JSONField(required=False, default=dict)

    def validate(self, attrs):
        known = set(self.fields.keys())
        extra = {}
        for k, v in self.initial_data.items():
            if k not in known:
                extra[k] = v
        if extra:
            attrs['_extra'] = extra
        return attrs


class SettingSerializer(serializers.Serializer):
    auto_approve = serializers.BooleanField(required=False)
    stale_threshold_seconds = serializers.IntegerField(required=False, min_value=300)
    scan_all_interval = serializers.IntegerField(required=False, min_value=300)
