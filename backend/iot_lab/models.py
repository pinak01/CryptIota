"""
QuantumGuard AI — IoT Security Lab ORM Models
Completely isolated from existing QuantumGuard tables.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, Text, Float, DateTime, Boolean
from database import Base


class IoTLabDevice(Base):
    """Registered IoT lab devices with hardware capability profile."""
    __tablename__ = "iot_lab_devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_name = Column(Text, nullable=False)
    device_type = Column(Text, nullable=False, default="simulated")  # esp32/rpi/simulated
    mac_address = Column(Text, unique=True, nullable=True)
    ip_address = Column(Text, nullable=True)
    firmware_version = Column(Text, default="1.0.0")
    cpu_mhz = Column(Integer, default=240)
    ram_kb = Column(Integer, default=520)
    supports_pqc = Column(Boolean, default=False)
    status = Column(Text, default="offline")  # online/offline
    handshake_mode = Column(Text, default="classical")  # pqc/classical/hybrid
    registered_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "mac_address": self.mac_address,
            "ip_address": self.ip_address,
            "firmware_version": self.firmware_version,
            "cpu_mhz": self.cpu_mhz,
            "ram_kb": self.ram_kb,
            "supports_pqc": self.supports_pqc,
            "status": self.status,
            "handshake_mode": self.handshake_mode,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class IoTLabSession(Base):
    """Cryptographic sessions with server-side and device-side metrics."""
    __tablename__ = "iot_lab_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, nullable=False, index=True)
    session_id = Column(Text, unique=True, nullable=False, index=True)
    mode = Column(Text, nullable=False)  # pqc/classical/hybrid
    handshake_time_ms = Column(Float, default=0.0)
    device_handshake_cpu_time_ms = Column(Float, nullable=True)
    device_free_heap_before = Column(Integer, nullable=True)
    device_free_heap_after = Column(Integer, nullable=True)
    public_key_bytes = Column(Integer, default=0)
    ciphertext_bytes = Column(Integer, default=0)
    shared_secret_hash = Column(Text, nullable=True)
    nonce_counter = Column(Integer, default=0)
    established_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=1))
    active = Column(Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "session_id": self.session_id,
            "mode": self.mode,
            "handshake_time_ms": self.handshake_time_ms,
            "device_handshake_cpu_time_ms": self.device_handshake_cpu_time_ms,
            "device_free_heap_before": self.device_free_heap_before,
            "device_free_heap_after": self.device_free_heap_after,
            "public_key_bytes": self.public_key_bytes,
            "ciphertext_bytes": self.ciphertext_bytes,
            "shared_secret_hash": self.shared_secret_hash,
            "nonce_counter": self.nonce_counter,
            "established_at": self.established_at.isoformat() if self.established_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "active": self.active,
        }


class IoTLabAttackLog(Base):
    """Attack detection event log."""
    __tablename__ = "iot_lab_attack_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Text, nullable=True)
    device_id = Column(Integer, nullable=True)
    attack_type = Column(Text, nullable=False)  # replay/downgrade/mitm/tampering
    severity = Column(Text, nullable=False, default="warning")  # info/warning/critical
    details = Column(Text, nullable=True)  # JSON text
    source_ip = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "attack_type": self.attack_type,
            "severity": self.severity,
            "details": self.details,
            "source_ip": self.source_ip,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


class IoTLabTelemetry(Base):
    """Encrypted telemetry records."""
    __tablename__ = "iot_lab_telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Text, nullable=False, index=True)
    device_id = Column(Integer, nullable=False)
    encrypted_payload = Column(Text, nullable=False)  # hex
    iv = Column(Text, nullable=False)  # hex
    tag = Column(Text, nullable=False)  # hex
    plaintext_preview = Column(Text, nullable=True)  # truncated first 64 chars
    payload_size_bytes = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "device_id": self.device_id,
            "encrypted_payload": self.encrypted_payload[:64] + "..." if self.encrypted_payload and len(self.encrypted_payload) > 64 else self.encrypted_payload,
            "iv": self.iv,
            "tag": self.tag,
            "plaintext_preview": self.plaintext_preview,
            "payload_size_bytes": self.payload_size_bytes,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
