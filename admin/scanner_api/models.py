from django.db import models


class Client(models.Model):
    registration_key = models.CharField(max_length=64, unique=True)
    hostname = models.CharField(max_length=255, default="")
    platform = models.CharField(max_length=128, default="")
    status = models.CharField(max_length=32, default="pending")
    last_seen = models.DateTimeField(null=True, blank=True)
    approved = models.BooleanField(default=False)

    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    vendor_name = models.CharField(max_length=255, default="", blank=True)
    vendor_contact = models.CharField(max_length=255, default="", blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    notes = models.TextField(default="", blank=True)

    scan_interval = models.IntegerField(default=3600)
    scan_enabled = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "clients"
        ordering = ["-last_seen"]

    def __str__(self):
        return f"{self.hostname} ({self.registration_key})"


class ScanResult(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="scans", null=True, blank=True)
    scan_type = models.CharField(max_length=32, default="scheduled")
    scan_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scan_results"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Scan {self.scan_type} for client {self.client_id} at {self.created_at}"


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


class Setting(models.Model):
    key = models.CharField(max_length=255, primary_key=True)
    value = models.TextField(blank=True)

    class Meta:
        db_table = "settings"

    def __str__(self):
        return self.key
