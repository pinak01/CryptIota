"""
QuantumGuard AI — IoT Security Lab: Flask Blueprint Routes
All endpoints are prefixed with /api/iot-lab
"""
import os
import json
import random
from datetime import datetime
from flask import Blueprint, request, jsonify

from database import get_db
from iot_lab.models import (
    IoTLabDevice, IoTLabSession, IoTLabAttackLog, IoTLabTelemetry,
)
from iot_lab import handshake as hs
from iot_lab import attack_detector as atk

iot_lab_bp = Blueprint("iot_lab", __name__, url_prefix="/api/iot-lab")


# ---------------------------------------------------------------------------
# Device Registration
# ---------------------------------------------------------------------------

@iot_lab_bp.route("/devices/register", methods=["POST"])
def register_device():
    data = request.get_json()
    if not data or "device_name" not in data:
        return jsonify({"error": "device_name is required"}), 400

    db = get_db()
    try:
        device = IoTLabDevice(
            device_name=data["device_name"],
            device_type=data.get("device_type", "simulated"),
            mac_address=data.get("mac_address"),
            ip_address=data.get("ip_address", request.remote_addr),
            firmware_version=data.get("firmware_version", "1.0.0"),
            cpu_mhz=data.get("cpu_mhz", 240),
            ram_kb=data.get("ram_kb", 520),
            supports_pqc=data.get("supports_pqc", False),
            status="online",
            handshake_mode=data.get("handshake_mode", "classical"),
        )
        db.add(device)
        db.commit()
        return jsonify(device.to_dict()), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@iot_lab_bp.route("/devices", methods=["GET"])
def list_devices():
    db = get_db()
    try:
        devices = db.query(IoTLabDevice).order_by(IoTLabDevice.registered_at.desc()).all()
        return jsonify({"devices": [d.to_dict() for d in devices], "total": len(devices)})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Handshake
# ---------------------------------------------------------------------------

@iot_lab_bp.route("/handshake/init", methods=["POST"])
def init_handshake():
    data = request.get_json()
    if not data or "device_id" not in data:
        return jsonify({"error": "device_id is required"}), 400

    device_id = data["device_id"]
    mode = data.get("mode", "pqc")

    db = get_db()
    try:
        device = db.query(IoTLabDevice).filter(IoTLabDevice.id == device_id).first()
        if not device:
            return jsonify({"error": f"Device {device_id} not found"}), 404

        # Check for downgrade attack
        atk.check_downgrade_on_handshake(device_id, mode, request.remote_addr)

        result = hs.handshake_init(device_id, mode)

        # Update device status
        device.status = "online"
        device.last_seen = datetime.utcnow()
        device.handshake_mode = mode
        db.commit()

        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()


@iot_lab_bp.route("/handshake/complete", methods=["POST"])
def complete_handshake():
    data = request.get_json()
    if not data or "session_id" not in data:
        return jsonify({"error": "session_id is required"}), 400

    try:
        result = hs.handshake_complete(data["session_id"], data)

        # Persist session to DB
        db = get_db()
        try:
            sess_info = hs.get_session(data["session_id"])
            db_session = IoTLabSession(
                device_id=sess_info["device_id"],
                session_id=data["session_id"],
                mode=result["mode"],
                handshake_time_ms=result["handshake_time_ms"],
                device_handshake_cpu_time_ms=data.get("device_cpu_time_ms"),
                device_free_heap_before=data.get("free_heap_before"),
                device_free_heap_after=data.get("free_heap_after"),
                public_key_bytes=result["public_key_bytes"],
                ciphertext_bytes=result["ciphertext_bytes"],
                shared_secret_hash=result["shared_secret_hash"],
                active=True,
            )
            db.add(db_session)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        return jsonify(result)
    except ValueError as e:
        # Possible MITM
        atk.detect_mitm(data["session_id"], str(e), source_ip=request.remote_addr)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

@iot_lab_bp.route("/telemetry", methods=["POST"])
def ingest_telemetry():
    data = request.get_json()
    if not data or "session_id" not in data:
        return jsonify({"error": "session_id is required"}), 400

    session_id = data["session_id"]
    encrypted_payload = data.get("encrypted_payload", "")
    iv = data.get("iv", "")
    tag = data.get("tag", "")
    nonce = data.get("nonce", 0)

    plaintext, attack_type = hs.process_telemetry(
        session_id, encrypted_payload, iv, tag, nonce
    )

    if attack_type:
        sess_info = hs.get_session(session_id)
        device_id = sess_info["device_id"] if sess_info else None

        if attack_type == "replay":
            atk.detect_replay(session_id, nonce, device_id, request.remote_addr)
        elif attack_type == "mitm":
            atk.detect_mitm(session_id, "Unknown or expired session", device_id, request.remote_addr)
        elif attack_type == "tampering":
            atk.detect_tampering(session_id, device_id, request.remote_addr)

        return jsonify({
            "status": "rejected",
            "reason": attack_type,
            "nonce": nonce,
        }), 403

    # Store telemetry
    db = get_db()
    try:
        sess_info = hs.get_session(session_id)
        preview = plaintext[:32].decode("utf-8", errors="replace") if plaintext else None

        entry = IoTLabTelemetry(
            session_id=session_id,
            device_id=sess_info["device_id"] if sess_info else 0,
            encrypted_payload=encrypted_payload[:128],
            iv=iv,
            tag=tag,
            plaintext_preview=preview,
            payload_size_bytes=len(plaintext) if plaintext else 0,
        )
        db.add(entry)

        # Update session nonce counter in DB
        db_sess = db.query(IoTLabSession).filter(
            IoTLabSession.session_id == session_id
        ).first()
        if db_sess:
            db_sess.nonce_counter = nonce

        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return jsonify({"status": "accepted", "nonce": nonce})


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

@iot_lab_bp.route("/sessions", methods=["GET"])
def list_sessions():
    db = get_db()
    try:
        sessions = (
            db.query(IoTLabSession)
            .order_by(IoTLabSession.established_at.desc())
            .limit(50)
            .all()
        )
        # Augment with in-memory state
        result = []
        for s in sessions:
            d = s.to_dict()
            mem_session = hs.get_session(s.session_id)
            if mem_session:
                d["nonce_counter"] = mem_session["nonce_counter"]
                d["active"] = True
            result.append(d)

        return jsonify({"sessions": result, "total": len(result)})
    finally:
        db.close()


@iot_lab_bp.route("/sessions/<session_id>", methods=["GET"])
def get_session_detail(session_id):
    db = get_db()
    try:
        session = db.query(IoTLabSession).filter(
            IoTLabSession.session_id == session_id
        ).first()
        if not session:
            return jsonify({"error": "Session not found"}), 404

        d = session.to_dict()

        # Get telemetry for this session
        telemetry = (
            db.query(IoTLabTelemetry)
            .filter(IoTLabTelemetry.session_id == session_id)
            .order_by(IoTLabTelemetry.timestamp.desc())
            .limit(50)
            .all()
        )
        d["telemetry"] = [t.to_dict() for t in telemetry]

        return jsonify(d)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Attack Logs
# ---------------------------------------------------------------------------

@iot_lab_bp.route("/attacks", methods=["GET"])
def list_attacks():
    db = get_db()
    try:
        query = db.query(IoTLabAttackLog)

        attack_type = request.args.get("type")
        if attack_type:
            query = query.filter(IoTLabAttackLog.attack_type == attack_type)

        severity = request.args.get("severity")
        if severity:
            query = query.filter(IoTLabAttackLog.severity == severity)

        total = query.count()
        attacks = query.order_by(IoTLabAttackLog.detected_at.desc()).limit(100).all()

        return jsonify({"attacks": [a.to_dict() for a in attacks], "total": total})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Lab Summary
# ---------------------------------------------------------------------------

@iot_lab_bp.route("/summary", methods=["GET"])
def lab_summary():
    db = get_db()
    try:
        total_devices = db.query(IoTLabDevice).count()
        online_devices = db.query(IoTLabDevice).filter(IoTLabDevice.status == "online").count()
        total_sessions = db.query(IoTLabSession).count()
        active_sessions = db.query(IoTLabSession).filter(IoTLabSession.active == True).count()

        # Average handshake time by mode
        from sqlalchemy import func
        avg_by_mode = {}
        for mode in ("pqc", "classical", "hybrid"):
            avg = db.query(func.avg(IoTLabSession.handshake_time_ms)).filter(
                IoTLabSession.mode == mode
            ).scalar()
            avg_by_mode[mode] = round(float(avg), 3) if avg else None

        total_telemetry = db.query(IoTLabTelemetry).count()

        attack_stats = atk.get_attack_stats()

        # Recent sessions for quick view
        recent_sessions = (
            db.query(IoTLabSession)
            .order_by(IoTLabSession.established_at.desc())
            .limit(5)
            .all()
        )

        return jsonify({
            "total_devices": total_devices,
            "online_devices": online_devices,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "avg_handshake_ms_by_mode": avg_by_mode,
            "total_telemetry_packets": total_telemetry,
            "attack_stats": attack_stats,
            "recent_sessions": [s.to_dict() for s in recent_sessions],
            "using_liboqs": hs.HAS_LIBOQS,
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Attack Simulation (for demos)
# ---------------------------------------------------------------------------

@iot_lab_bp.route("/simulate/replay", methods=["POST"])
def simulate_replay():
    """Simulate a full device lifecycle then trigger a replay attack."""
    db = get_db()
    try:
        # Step 1: Get or create a simulated device
        device = db.query(IoTLabDevice).filter(IoTLabDevice.device_type == "simulated").first()
        if not device:
            device = IoTLabDevice(
                device_name="Sim-Replay-Device",
                device_type="simulated",
                mac_address=f"SIM:{os.urandom(3).hex().upper()}",
                cpu_mhz=240, ram_kb=520, supports_pqc=True,
                status="online",
            )
            db.add(device)
            db.commit()

        device_id = device.id
    finally:
        db.close()

    # Step 2: Full handshake
    init_result = hs.handshake_init(device_id, "pqc")
    session_id = init_result["session_id"]

    # Simulate device sending ciphertext
    if hs.HAS_LIBOQS:
        import oqs
        kem = oqs.KeyEncapsulation("ML-KEM-512")
        server_pk = bytes.fromhex(init_result["server_public_key"])
        ciphertext, _ = kem.encap_secret(server_pk)
        ct_hex = ciphertext.hex()
    else:
        ct_hex = os.urandom(768).hex()

    hs.handshake_complete(session_id, {
        "device_ciphertext": ct_hex,
        "device_cpu_time_ms": round(random.uniform(30, 80), 2),
        "free_heap_before": random.randint(250000, 300000),
        "free_heap_after": random.randint(200000, 250000),
    })

    # Step 3: Send legitimate telemetry
    payload, iv, tag, nonce = hs.encrypt_telemetry(
        session_id, b'{"temp": 23.5, "humidity": 67}'
    )
    hs.process_telemetry(session_id, payload, iv, tag, nonce)

    # Step 4: Replay the same telemetry (same nonce!)
    _, attack_type = hs.process_telemetry(session_id, payload, iv, tag, nonce)

    # Log the attack
    attack_entry = atk.detect_replay(session_id, nonce, device_id, "192.168.1.100")

    # Persist session
    _persist_simulation_session(session_id, device_id)

    return jsonify({
        "simulation": "replay",
        "result": "Replay attack detected and logged",
        "attack_log": attack_entry,
        "session_id": session_id,
        "replayed_nonce": nonce,
    })


@iot_lab_bp.route("/simulate/downgrade", methods=["POST"])
def simulate_downgrade():
    """Simulate a device previously using PQC now requesting classical."""
    db = get_db()
    try:
        # Create or find a device that was using PQC
        device = db.query(IoTLabDevice).filter(
            IoTLabDevice.device_name == "Sim-Downgrade-Device"
        ).first()
        if not device:
            device = IoTLabDevice(
                device_name="Sim-Downgrade-Device",
                device_type="simulated",
                mac_address=f"SIM:{os.urandom(3).hex().upper()}",
                cpu_mhz=240, ram_kb=520, supports_pqc=True,
                status="online",
                handshake_mode="pqc",  # Was using PQC
            )
            db.add(device)
            db.commit()
        else:
            device.handshake_mode = "pqc"
            db.commit()

        device_id = device.id
    finally:
        db.close()

    # Attempt handshake with classical (downgrade!)
    attack_entry = atk.detect_downgrade(
        device_id, "pqc", "classical", "192.168.1.101"
    )

    # Do the classical handshake anyway
    init_result = hs.handshake_init(device_id, "classical")
    session_id = init_result["session_id"]

    # Complete with simulated ECDH
    hs.handshake_complete(session_id, {
        "device_cpu_time_ms": round(random.uniform(5, 15), 2),
        "free_heap_before": random.randint(280000, 300000),
        "free_heap_after": random.randint(275000, 295000),
    })

    _persist_simulation_session(session_id, device_id)

    return jsonify({
        "simulation": "downgrade",
        "result": "Downgrade attack detected: PQC → Classical",
        "attack_log": attack_entry,
        "session_id": session_id,
    })


@iot_lab_bp.route("/simulate/mitm", methods=["POST"])
def simulate_mitm():
    """Simulate a MITM attack by sending invalid ciphertext."""
    db = get_db()
    try:
        device = db.query(IoTLabDevice).filter(IoTLabDevice.device_type == "simulated").first()
        if not device:
            device = IoTLabDevice(
                device_name="Sim-MITM-Device",
                device_type="simulated",
                mac_address=f"SIM:{os.urandom(3).hex().upper()}",
                cpu_mhz=240, ram_kb=520, supports_pqc=True,
                status="online",
            )
            db.add(device)
            db.commit()

        device_id = device.id
    finally:
        db.close()

    # Start handshake
    init_result = hs.handshake_init(device_id, "pqc")
    session_id = init_result["session_id"]

    # MITM: send garbage ciphertext
    try:
        hs.handshake_complete(session_id, {
            "device_ciphertext": os.urandom(768).hex(),
            "device_cpu_time_ms": 0,
            "free_heap_before": 0,
            "free_heap_after": 0,
        })
        # If using simulated PQC, it "succeeds" but the key is wrong.
        # Send telemetry with bad key to trigger tampering detection
        if hs.get_session_key_exists(session_id):
            fake_payload = os.urandom(32).hex()
            fake_iv = os.urandom(12).hex()
            fake_tag = os.urandom(16).hex()
            _, attack_type = hs.process_telemetry(session_id, fake_payload, fake_iv, fake_tag, 1)
            if attack_type:
                attack_entry = atk.detect_tampering(session_id, device_id, "192.168.1.102")
            else:
                attack_entry = atk.detect_mitm(session_id, "Forged ciphertext accepted (simulated)", device_id, "192.168.1.102")
        else:
            attack_entry = atk.detect_mitm(session_id, "Key derivation failed", device_id, "192.168.1.102")
    except Exception as e:
        attack_entry = atk.detect_mitm(session_id, str(e), device_id, "192.168.1.102")

    return jsonify({
        "simulation": "mitm",
        "result": "MITM attack simulated — session validation failure logged",
        "attack_log": attack_entry,
        "session_id": session_id,
    })


def _persist_simulation_session(session_id: str, device_id: int):
    """Persist a simulated session to the database."""
    sess_info = hs.get_session(session_id)
    if not sess_info:
        return

    db = get_db()
    try:
        existing = db.query(IoTLabSession).filter(
            IoTLabSession.session_id == session_id
        ).first()
        if not existing:
            db_session = IoTLabSession(
                device_id=device_id,
                session_id=session_id,
                mode=sess_info.get("mode", "pqc"),
                handshake_time_ms=sess_info.get("handshake_time_ms", 0),
                device_handshake_cpu_time_ms=sess_info.get("device_cpu_time_ms"),
                device_free_heap_before=sess_info.get("device_free_heap_before"),
                device_free_heap_after=sess_info.get("device_free_heap_after"),
                public_key_bytes=sess_info.get("key_bytes_actual", 0),
                ciphertext_bytes=sess_info.get("ciphertext_bytes", 0),
                shared_secret_hash=sess_info.get("shared_secret_hash", ""),
                nonce_counter=sess_info.get("nonce_counter", 0),
                active=True,
            )
            db.add(db_session)
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
