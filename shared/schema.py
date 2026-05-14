from dataclasses import dataclass, field, asdict
from typing import Optional


def serialize(obj):
    return asdict(obj)


@dataclass
class RegistrationRequest:
    registration_key: str
    hostname: str
    platform: str


@dataclass
class PingRequest:
    registration_key: str
    hostname: str


@dataclass
class ScanData:
    registration_key: str
    hostname: str
    scan_type: str
    processor: dict = field(default_factory=dict)
    ram: dict = field(default_factory=dict)
    storage: dict = field(default_factory=dict)
    partitions: list = field(default_factory=list)
    gpu: list = field(default_factory=list)
    motherboard: dict = field(default_factory=dict)
    os_info: dict = field(default_factory=dict)
    accounts: list = field(default_factory=list)
    network: dict = field(default_factory=dict)
    peripherals: dict = field(default_factory=dict)
    software: list = field(default_factory=list)
    updates: list = field(default_factory=list)
    monitor: dict = field(default_factory=dict)
    antivirus: dict = field(default_factory=dict)
    raw_json: str = ""


@dataclass
class ManualUpdate:
    purchase_cost: Optional[float] = None
    purchase_date: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_contact: Optional[str] = None
    warranty_expiry: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class AddonDevice:
    name: str
    description: str = ""
    serial_number: str = ""
    purchase_cost: Optional[float] = None
    category: str = ""


@dataclass
class ScanConfig:
    interval_seconds: int = 3600
    enabled: bool = True
