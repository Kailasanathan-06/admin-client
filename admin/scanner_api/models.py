import uuid
from django.db import models
from django.utils import timezone


class ClientGroup(models.Model):
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "client_groups"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Client(models.Model):
    registration_key = models.CharField(max_length=64, unique=True, db_index=True)
    hostname = models.CharField(max_length=255, default="")
    platform = models.CharField(max_length=128, default="")
    status = models.CharField(max_length=32, default="pending")
    last_seen = models.DateTimeField(null=True, blank=True)
    approved = models.BooleanField(default=False)

    group = models.ForeignKey(ClientGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="clients")
    tags = models.CharField(max_length=512, default="", blank=True, help_text="Comma-separated tags")

    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    vendor_name = models.CharField(max_length=255, default="", blank=True)
    vendor_contact = models.CharField(max_length=255, default="", blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    notes = models.TextField(default="", blank=True)

    scan_interval = models.IntegerField(default=3600)
    scan_enabled = models.BooleanField(default=True)
    scan_requested = models.BooleanField(default=False)

    client_version = models.CharField(max_length=32, default="", blank=True)
    os_version = models.CharField(max_length=256, default="", blank=True)
    cpu_model = models.CharField(max_length=256, default="", blank=True)
    ram_info = models.CharField(max_length=128, default="", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "clients"
        ordering = ["-last_seen"]

    def __str__(self):
        return f"{self.hostname} ({self.registration_key})"

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()] if self.tags else []

    @property
    def is_stale(self):
        if not self.last_seen:
            return True
        threshold = timezone.now() - timezone.timedelta(seconds=max(self.scan_interval * 2, 7200))
        return self.last_seen < threshold


class ScanResult(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="scans", null=True, blank=True)
    scan_type = models.CharField(max_length=32, default="scheduled")
    scan_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scan_results"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["client", "-created_at"])]

    def __str__(self):
        return f"Scan {self.scan_type} for {self.client_id} at {self.created_at}"


class AddonDevice(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="addons")
    name = models.CharField(max_length=255)
    description = models.TextField(default="", blank=True)
    serial_number = models.CharField(max_length=255, default="", blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=128, default="", blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "addon_devices"
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ("register", "Client Registered"),
        ("approve", "Client Approved"),
        ("scan", "Scan Completed"),
        ("scan_request", "Scan Requested"),
        ("delete", "Client Deleted"),
        ("update", "Client Updated"),
        ("login", "Admin Login"),
        ("setting_change", "Setting Changed"),
    ]

    action = models.CharField(max_length=32, choices=ACTION_CHOICES)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name="activity_logs")
    details = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "activity_logs"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self):
        return f"{self.action} at {self.created_at}"


class Setting(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    value = models.TextField(blank=True)

    class Meta:
        db_table = "settings"

    def __str__(self):
        return self.key

    @classmethod
    def get(cls, key, default=""):
        obj = cls.objects.filter(key=key).first()
        return obj.value if obj else default

    @classmethod
    def set(cls, key, value):
        cls.objects.update_or_create(key=key, defaults={"value": str(value)})
