"""
QuantumGuard AI — IoT Security Lab: Attack Detection Engine
Detects replay, downgrade, MITM, and tampering attacks.
"""
import json
from datetime import datetime
from database import get_db
from iot_lab.models import IoTLabAttackLog, IoTLabDevice


def log_attack(attack_type: str, severity: str, details: dict,
               session_id: str = None, device_id: int = None,
               source_ip: str = None):
    """Persist an attack event to the database."""
    db = get_db()
    try:
        entry = IoTLabAttackLog(
            session_id=session_id,
            device_id=device_id,
            attack_type=attack_type,
            severity=severity,
            details=json.dumps(details),
            source_ip=source_ip,
            detected_at=datetime.utcnow(),
        )
        db.add(entry)
        db.commit()
        return entry.to_dict()
    except Exception:
        db.rollback()
        return None
    finally:
        db.close()


def detect_replay(session_id: str, nonce: int, device_id: int = None,
                  source_ip: str = None):
    """Log a replay attack detection."""
    return log_attack(
        attack_type="replay",
        severity="critical",
        details={
            "description": "Nonce reuse detected — potential replay attack",
            "nonce_value": nonce,
            "action": "Telemetry packet rejected",
        },
        session_id=session_id,
        device_id=device_id,
        source_ip=source_ip,
    )


def detect_downgrade(device_id: int, old_mode: str, new_mode: str,
                     source_ip: str = None):
    """Log a downgrade attack detection."""
    mode_rank = {"pqc": 3, "hybrid": 2, "classical": 1}
    old_rank = mode_rank.get(old_mode, 0)
    new_rank = mode_rank.get(new_mode, 0)

    if new_rank < old_rank:
        severity = "critical" if old_mode == "pqc" and new_mode == "classical" else "warning"
        return log_attack(
            attack_type="downgrade",
            severity=severity,
            details={
                "description": f"Handshake mode downgrade: {old_mode} → {new_mode}",
                "previous_mode": old_mode,
                "requested_mode": new_mode,
                "action": "Handshake allowed but flagged for review",
            },
            device_id=device_id,
            source_ip=source_ip,
        )
    return None


def detect_mitm(session_id: str, reason: str, device_id: int = None,
                source_ip: str = None):
    """Log a suspected MITM attack."""
    return log_attack(
        attack_type="mitm",
        severity="critical",
        details={
            "description": "Session validation failure — potential MITM attack",
            "reason": reason,
            "action": "Session rejected",
        },
        session_id=session_id,
        device_id=device_id,
        source_ip=source_ip,
    )


def detect_tampering(session_id: str, device_id: int = None,
                     source_ip: str = None):
    """Log a telemetry tampering detection."""
    return log_attack(
        attack_type="tampering",
        severity="critical",
        details={
            "description": "AES-GCM authentication tag mismatch — telemetry tampered",
            "action": "Telemetry packet rejected, session flagged",
        },
        session_id=session_id,
        device_id=device_id,
        source_ip=source_ip,
    )


def check_downgrade_on_handshake(device_id: int, requested_mode: str,
                                  source_ip: str = None):
    """
    Check if the requested handshake mode is a downgrade from the device's
    last known mode. Returns the attack log entry if downgrade detected.
    """
    db = get_db()
    try:
        device = db.query(IoTLabDevice).filter(IoTLabDevice.id == device_id).first()
        if device and device.handshake_mode:
            return detect_downgrade(
                device_id=device_id,
                old_mode=device.handshake_mode,
                new_mode=requested_mode,
                source_ip=source_ip,
            )
        return None
    finally:
        db.close()


def get_attack_stats():
    """Return aggregate attack statistics."""
    db = get_db()
    try:
        total = db.query(IoTLabAttackLog).count()
        by_type = {}
        for atype in ("replay", "downgrade", "mitm", "tampering"):
            by_type[atype] = db.query(IoTLabAttackLog).filter(
                IoTLabAttackLog.attack_type == atype
            ).count()

        by_severity = {}
        for sev in ("info", "warning", "critical"):
            by_severity[sev] = db.query(IoTLabAttackLog).filter(
                IoTLabAttackLog.severity == sev
            ).count()

        return {
            "total_attacks": total,
            "by_type": by_type,
            "by_severity": by_severity,
        }
    finally:
        db.close()
