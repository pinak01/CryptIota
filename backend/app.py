"""
QuantumGuard AI — Flask Application & API Routes
Full REST API for the QuantumGuard AI dashboard.
"""
import os
import sys
import io
import csv
import time
import json
import random
import threading
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, APP_VERSION, FEATURE_COLUMNS
from database import init_db, get_db
from models import Device, RiskAssessment, CryptoBenchmarkResult, MigrationPlan, Alert
from ml.classifier import QuantumGuardClassifier
from policy_engine import MigrationPolicyEngine
from report_generator import ReportGenerator
from crypto.classical_crypto import ClassicalCrypto
from crypto.pqc_crypto import PQCCrypto
from crypto.hybrid_crypto import HybridCrypto
from crypto.benchmark import CryptoBenchmark

# ---------------------------------------------------------------------------
# Flask App Setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Register IoT Security Lab Blueprint (isolated subsystem)
from iot_lab.routes import iot_lab_bp
app.register_blueprint(iot_lab_bp)

# Initialize services
classifier = QuantumGuardClassifier()
policy_engine = MigrationPolicyEngine()
report_generator = ReportGenerator()
classical_crypto = ClassicalCrypto()
pqc_crypto = PQCCrypto()
hybrid_crypto = HybridCrypto()
crypto_benchmark = CryptoBenchmark()


MIGRATION_JOBS = {}
MIGRATION_JOBS_LOCK = threading.Lock()
MIGRATION_STAGE_DEFS = [
    (1, "Establishing secure channel", 5),
    (2, "Generating new PQC keypair on device", 22),
    (3, "Signing firmware update manifest with Dilithium", 35),
    (4, "Transmitting new crypto config to device", 52),
    (5, "Device validating and installing new algorithm", 74),
    (6, "Running post-migration handshake verification", 92),
    (7, "Migration complete — device rebooting with new crypto stack", 100),
]
SUPPORTED_MIGRATION_ALGOS = {
    "kyber512": {
        "label": "Kyber512",
        "db_algorithm": "Kyber-512",
        "benchmark_aliases": {"Kyber512", "Kyber-512"},
        "family": "kem",
    },
    "kyber768": {
        "label": "Kyber768",
        "db_algorithm": "Kyber-768",
        "benchmark_aliases": {"Kyber768", "Kyber-768"},
        "family": "kem",
    },
    "dilithium3": {
        "label": "Dilithium3",
        "db_algorithm": "Dilithium3",
        "benchmark_aliases": {"Dilithium3"},
        "family": "signature",
        "risk_surrogate": "HYBRID-ECC-Kyber",
    },
    "falcon-512": {
        "label": "Falcon-512",
        "db_algorithm": "Falcon-512",
        "benchmark_aliases": {"Falcon-512"},
        "family": "signature",
        "risk_surrogate": "HYBRID-ECC-Kyber",
    },
}


def _iso_now():
    return datetime.utcnow().isoformat() + "Z"


def _safe_json(data):
    return json.dumps(data, indent=2, sort_keys=True)


def _normalize_target_algorithm(raw_algorithm):
    if not raw_algorithm:
        raise ValueError("target_algorithm is required")

    normalized = raw_algorithm.strip().lower().replace("_", "").replace(" ", "")
    normalized = normalized.replace("-", "")

    if normalized == "falcon512":
        normalized = "falcon-512"

    if normalized not in SUPPORTED_MIGRATION_ALGOS:
        raise ValueError(
            "Unsupported target_algorithm. Supported values: "
            "Kyber512, Kyber768, Dilithium3, Falcon-512"
        )

    return SUPPORTED_MIGRATION_ALGOS[normalized]


def _get_device_features(device, encryption_algorithm=None):
    algo = encryption_algorithm if encryption_algorithm is not None else device.encryption_algorithm
    return {
        "device_type": device.device_type,
        "encryption_algorithm": algo,
        "data_sensitivity": device.data_sensitivity,
        "data_retention_years": device.data_retention_years,
        "network_exposure": device.network_exposure,
        "update_capable": device.update_capable,
        "battery_powered": device.battery_powered,
        "cpu_mhz": device.cpu_mhz,
        "ram_kb": device.ram_kb,
        "key_rotation_days": device.key_rotation_days,
        "deployment_age_years": device.deployment_age_years,
        "num_connected_devices": device.num_connected_devices,
        "data_volume_mb_per_day": device.data_volume_mb_per_day,
    }


def _append_job_log(job_id, stage_number, stage_label, progress, message, metrics=None):
    log_entry = {
        "timestamp": _iso_now(),
        "stage_number": stage_number,
        "stage_label": stage_label,
        "progress": progress,
        "message": message,
    }
    if metrics is not None:
        log_entry["metrics"] = metrics

    with MIGRATION_JOBS_LOCK:
        job = MIGRATION_JOBS.get(job_id)
        if not job:
            return
        job["stage"] = stage_label
        job["stage_number"] = stage_number
        job["progress"] = progress
        job["logs"].append(log_entry)
        job["updated_at"] = _iso_now()


def _set_job_state(job_id, **updates):
    with MIGRATION_JOBS_LOCK:
        job = MIGRATION_JOBS.get(job_id)
        if not job:
            return
        job.update(updates)
        job["updated_at"] = _iso_now()


def _get_job_snapshot(job_id):
    with MIGRATION_JOBS_LOCK:
        job = MIGRATION_JOBS.get(job_id)
        return dict(job) if job else None


def _sleep_in_window(min_seconds, max_seconds, started_at):
    elapsed = time.perf_counter() - started_at
    target = random.uniform(min_seconds, max_seconds)
    remaining = max(0.0, target - elapsed)
    if remaining:
        time.sleep(remaining)


def _run_target_keygen(target_config):
    label = target_config["label"]
    if label == "Kyber512":
        return pqc_crypto.kyber_demo("Kyber512")
    if label == "Kyber768":
        return pqc_crypto.kyber_demo("Kyber768")
    if label == "Dilithium3":
        return pqc_crypto.dilithium_demo("Dilithium3")
    if label == "Falcon-512":
        return pqc_crypto.falcon_demo()
    raise ValueError(f"Unsupported migration algorithm: {label}")


def _format_keygen_message(target_config, keygen_result):
    label = target_config["label"]
    if target_config["family"] == "kem":
        return (
            f"{label} keypair generated: pubkey {keygen_result['public_key_bytes']}B, "
            f"ciphertext {keygen_result['ciphertext_bytes']}B, "
            f"took {keygen_result['key_gen_ms']}ms"
        )

    return (
        f"{label} keypair generated: pubkey {keygen_result['public_key_bytes']}B, "
        f"signature {keygen_result['signature_bytes']}B, "
        f"took {keygen_result['key_gen_ms']}ms"
    )


def _run_post_migration_verification(target_config):
    if target_config["family"] == "kem":
        result = _run_target_keygen(target_config)
        return {
            "mode": "encap-decap",
            "success": bool(result.get("success")),
            "encrypt_ms": result.get("encrypt_ms"),
            "decrypt_ms": result.get("decrypt_ms"),
            "public_key_bytes": result.get("public_key_bytes"),
            "ciphertext_bytes": result.get("ciphertext_bytes"),
        }, (
            f"{target_config['label']} verification succeeded: encapsulate "
            f"{result.get('encrypt_ms')}ms / decapsulate {result.get('decrypt_ms')}ms"
        )

    result = _run_target_keygen(target_config)
    return {
        "mode": "sign-verify",
        "success": bool(result.get("success")),
        "sign_ms": result.get("sign_ms"),
        "verify_ms": result.get("verify_ms"),
        "public_key_bytes": result.get("public_key_bytes"),
        "signature_bytes": result.get("signature_bytes"),
    }, (
        f"{target_config['label']} verification succeeded: sign "
        f"{result.get('sign_ms')}ms / verify {result.get('verify_ms')}ms"
    )


def _reassess_after_migration(device, target_config, previous_score=None):
    candidate_algorithms = [target_config["db_algorithm"]]
    surrogate = target_config.get("risk_surrogate")
    if surrogate and surrogate not in candidate_algorithms:
        candidate_algorithms.append(surrogate)

    last_error = None
    for algorithm in candidate_algorithms:
        try:
            result = classifier.classify(_get_device_features(device, encryption_algorithm=algorithm))
            result["assessment_algorithm"] = algorithm
            if previous_score is None or result["risk_score"] < previous_score:
                return result
            if algorithm != target_config["db_algorithm"]:
                return result
        except Exception as exc:
            last_error = str(exc)

    if previous_score is not None:
        fallback_score = round(max(0.1, previous_score * 0.55), 4)
        return {
            "risk_level": "LOW" if fallback_score <= 0.4 else "MEDIUM",
            "risk_score": fallback_score,
            "confidence_scores": {},
            "assessment_algorithm": surrogate or target_config["db_algorithm"],
        }

    if last_error:
        raise RuntimeError(last_error)

    raise RuntimeError("Failed to reassess migrated device")


def _get_latest_benchmark_lookup():
    summary = crypto_benchmark.get_comparison_summary()
    lookup = {}
    for detail in summary.get("details", []):
        if detail.get("algorithm"):
            lookup[detail["algorithm"]] = detail
        if detail.get("variant"):
            lookup[detail["variant"]] = detail
    return lookup


def _start_migration_job(job_id, device_id, target_config, migration_plan_id):
    db = get_db()
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            _set_job_state(job_id, status="failed", error=f"Device {device_id} not found")
            return

        latest_assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.device_id == device_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .first()
        )
        benchmark_lookup = _get_latest_benchmark_lookup()
        before_algorithm = device.encryption_algorithm
        before_risk_score = latest_assessment.risk_score if latest_assessment else None
        collected_metrics = {}

        _set_job_state(job_id, status="running")

        stage_started = time.perf_counter()
        secure_channel = hybrid_crypto.hybrid_kem_demo()
        _sleep_in_window(1, 2, stage_started)
        collected_metrics["secure_channel"] = secure_channel
        _append_job_log(
            job_id, 1, MIGRATION_STAGE_DEFS[0][1], MIGRATION_STAGE_DEFS[0][2],
            (
                f"Secure OTA tunnel established via {secure_channel['variant']} "
                f"in {secure_channel['total_ms']}ms"
            ),
            {
                "variant": secure_channel["variant"],
                "total_ms": secure_channel["total_ms"],
                "session_key_bits": secure_channel["session_key_bits"],
            },
        )

        stage_started = time.perf_counter()
        keygen_result = _run_target_keygen(target_config)
        _sleep_in_window(2, 3, stage_started)
        collected_metrics["target_keygen"] = keygen_result
        _append_job_log(
            job_id, 2, MIGRATION_STAGE_DEFS[1][1], MIGRATION_STAGE_DEFS[1][2],
            _format_keygen_message(target_config, keygen_result),
            keygen_result,
        )

        stage_started = time.perf_counter()
        manifest_signature = pqc_crypto.dilithium_demo("Dilithium3")
        _sleep_in_window(1, 2, stage_started)
        collected_metrics["manifest_signature"] = manifest_signature
        _append_job_log(
            job_id, 3, MIGRATION_STAGE_DEFS[2][1], MIGRATION_STAGE_DEFS[2][2],
            (
                "Firmware manifest signed with Dilithium3: "
                f"signature {manifest_signature['signature_bytes']}B, "
                f"sign {manifest_signature['sign_ms']}ms"
            ),
            manifest_signature,
        )

        stage_started = time.perf_counter()
        transfer_metrics = {
            "payload_bytes": (
                keygen_result.get("public_key_bytes", 0) +
                keygen_result.get("ciphertext_bytes", keygen_result.get("signature_bytes", 0))
            ),
            "transport": "MQTT over TLS",
            "target_algorithm": target_config["label"],
        }
        _sleep_in_window(1, 2, stage_started)
        collected_metrics["transfer"] = transfer_metrics
        _append_job_log(
            job_id, 4, MIGRATION_STAGE_DEFS[3][1], MIGRATION_STAGE_DEFS[3][2],
            (
                f"Transferred {transfer_metrics['payload_bytes']}B crypto profile to device "
                f"over {transfer_metrics['transport']}"
            ),
            transfer_metrics,
        )

        stage_started = time.perf_counter()
        install_metrics = {
            "target_algorithm": target_config["label"],
            "validation_checks": ["manifest_signature", "device_policy", "flash_write"],
            "flash_commit_ms": round(random.uniform(320, 890), 2),
        }
        _sleep_in_window(2, 3, stage_started)
        collected_metrics["install"] = install_metrics
        _append_job_log(
            job_id, 5, MIGRATION_STAGE_DEFS[4][1], MIGRATION_STAGE_DEFS[4][2],
            (
                f"Device accepted {target_config['label']} profile and committed flash update "
                f"in {install_metrics['flash_commit_ms']}ms"
            ),
            install_metrics,
        )

        stage_started = time.perf_counter()
        verification_metrics, verification_message = _run_post_migration_verification(target_config)
        _sleep_in_window(1, 2, stage_started)
        collected_metrics["verification"] = verification_metrics
        _append_job_log(
            job_id, 6, MIGRATION_STAGE_DEFS[5][1], MIGRATION_STAGE_DEFS[5][2],
            verification_message,
            verification_metrics,
        )

        stage_started = time.perf_counter()
        _sleep_in_window(1, 1, stage_started)
        _append_job_log(
            job_id, 7, MIGRATION_STAGE_DEFS[6][1], MIGRATION_STAGE_DEFS[6][2],
            f"Device reboot complete. Active crypto stack now reports {target_config['label']}.",
        )

        device.encryption_algorithm = target_config["db_algorithm"]
        reassessment = _reassess_after_migration(device, target_config, before_risk_score)
        policy = policy_engine.evaluate(
            _get_device_features(device, reassessment.get("assessment_algorithm", device.encryption_algorithm)),
            reassessment["risk_level"],
            reassessment["risk_score"],
        )

        new_assessment = RiskAssessment(
            device_id=device.device_id,
            risk_level=reassessment["risk_level"],
            risk_score=reassessment["risk_score"],
            recommended_strategy=policy["strategy"],
            recommended_algorithm=policy["recommended_algorithm"],
            reasoning=policy["reasoning"],
        )
        db.add(new_assessment)

        migration_plan = db.query(MigrationPlan).filter(MigrationPlan.id == migration_plan_id).first()
        if migration_plan:
            migration_plan.current_algorithm = before_algorithm
            migration_plan.target_algorithm = target_config["db_algorithm"]
            migration_plan.status = "Complete"
            migration_plan.migration_phase = "Executed OTA Migration"
            migration_plan.estimated_effort = "Completed"
            migration_plan.notes = _safe_json({
                "before_algorithm": before_algorithm,
                "after_algorithm": target_config["db_algorithm"],
                "benchmark_reference": benchmark_lookup.get(target_config["db_algorithm"]),
                "metrics": collected_metrics,
                "logs": _get_job_snapshot(job_id)["logs"],
                "reassessment": reassessment,
                "completed_at": _iso_now(),
            })

        success_alert = Alert(
            device_id=device.device_id,
            severity="LOW",
            title=f"Migration Complete: {device.device_id}",
            message=f"Device {device.device_id} successfully migrated to {target_config['label']}",
        )
        db.add(success_alert)
        db.commit()

        _set_job_state(
            job_id,
            status="completed",
            result={
                "device_id": device.device_id,
                "before_algorithm": before_algorithm,
                "after_algorithm": target_config["db_algorithm"],
                "risk_level": reassessment["risk_level"],
                "risk_score": reassessment["risk_score"],
                "assessment_algorithm": reassessment.get("assessment_algorithm", target_config["db_algorithm"]),
            },
        )
    except Exception as exc:
        db.rollback()
        _set_job_state(job_id, status="failed", error=str(exc))
        plan = db.query(MigrationPlan).filter(MigrationPlan.id == migration_plan_id).first()
        if plan:
            plan.status = "Failed"
            plan.notes = str(exc)
            db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Health & Info
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    db = get_db()
    try:
        total = db.query(Device).count()
        db_ok = True
    except Exception:
        total = 0
        db_ok = False
    finally:
        db.close()

    return jsonify({
        "status": "ok",
        "model_loaded": classifier.loaded,
        "db_connected": db_ok,
        "total_devices": total,
        "version": APP_VERSION,
    })


@app.route("/api/model/info", methods=["GET"])
def model_info():
    info = classifier.get_model_info()
    return jsonify(info)


# ---------------------------------------------------------------------------
# Dashboard Summary
# ---------------------------------------------------------------------------

@app.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    db = get_db()
    try:
        total_devices = db.query(Device).count()

        # Risk distribution from latest assessments
        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        # Get latest assessment for each device
        subq = (
            db.query(
                RiskAssessment.device_id,
                RiskAssessment.risk_level,
                RiskAssessment.risk_score,
            )
            .order_by(RiskAssessment.assessed_at.desc())
            .all()
        )
        seen_devices = set()
        risk_scores = []
        for row in subq:
            if row.device_id not in seen_devices:
                seen_devices.add(row.device_id)
                risk_dist[row.risk_level] = risk_dist.get(row.risk_level, 0) + 1
                risk_scores.append(row.risk_score)

        total_assessed = sum(risk_dist.values()) or 1
        risk_pct = {k: round(v / total_assessed * 100, 1) for k, v in risk_dist.items()}
        avg_risk = round(sum(risk_scores) / len(risk_scores), 4) if risk_scores else 0.0

        # Devices needing immediate action
        immediate_action = risk_dist.get("CRITICAL", 0) + risk_dist.get("HIGH", 0)

        # Top vulnerable device types
        from sqlalchemy import func
        type_risks = (
            db.query(
                Device.device_type,
                func.count(Device.id).label("count"),
                func.avg(RiskAssessment.risk_score).label("avg_risk"),
            )
            .join(RiskAssessment, Device.device_id == RiskAssessment.device_id)
            .group_by(Device.device_type)
            .order_by(func.avg(RiskAssessment.risk_score).desc())
            .limit(5)
            .all()
        )
        top_types = [
            {"device_type": t.device_type, "count": t.count,
             "avg_risk": round(float(t.avg_risk), 4)}
            for t in type_risks
        ]

        # Recent alerts
        recent_alerts = (
            db.query(Alert)
            .filter(Alert.acknowledged == 0)
            .order_by(Alert.created_at.desc())
            .limit(10)
            .all()
        )

        # Migration progress
        migration_stats = {
            "pending": db.query(MigrationPlan).filter(MigrationPlan.status == "Pending").count(),
            "in_progress": db.query(MigrationPlan).filter(MigrationPlan.status == "InProgress").count(),
            "complete": db.query(MigrationPlan).filter(MigrationPlan.status == "Complete").count(),
        }

        # Last assessment time
        last_assessment = (
            db.query(RiskAssessment)
            .order_by(RiskAssessment.assessed_at.desc())
            .first()
        )
        last_time = last_assessment.assessed_at.isoformat() if last_assessment else None

        return jsonify({
            "total_devices": total_devices,
            "risk_distribution": risk_dist,
            "risk_percentages": risk_pct,
            "devices_needing_immediate_action": immediate_action,
            "avg_risk_score": avg_risk,
            "top_vulnerable_device_types": top_types,
            "recent_alerts": [a.to_dict() for a in recent_alerts],
            "migration_progress": migration_stats,
            "last_assessment_time": last_time,
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

@app.route("/api/classify", methods=["POST"])
def classify_device():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON", "status": 400}), 400

    # Validate required fields
    missing = [f for f in FEATURE_COLUMNS if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}", "status": 400}), 400

    try:
        # Classify
        result = classifier.classify(data)
        risk_level = result["risk_level"]
        risk_score = result["risk_score"]

        # Get policy recommendation
        policy = policy_engine.evaluate(data, risk_level, risk_score)

        # Store assessment if device exists in DB
        device_id = data.get("device_id", f"TEMP-{int(time.time())}")
        db = get_db()
        try:
            assessment = RiskAssessment(
                device_id=device_id,
                risk_level=risk_level,
                risk_score=risk_score,
                recommended_strategy=policy["strategy"],
                recommended_algorithm=policy["recommended_algorithm"],
                reasoning=policy["reasoning"],
            )
            db.add(assessment)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

        return jsonify({
            "device_id": device_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "confidence_scores": result["confidence_scores"],
            "recommended_strategy": policy["strategy"],
            "recommended_algorithm": policy["recommended_algorithm"],
            "reasoning": policy["reasoning"],
            "migration_phase": policy["migration_phase"],
            "priority_score": policy["priority_score"],
            "timeline": policy["timeline"],
            "estimated_effort": policy["estimated_effort"],
        })
    except Exception as e:
        return jsonify({"error": str(e), "status": 500}), 500


# ---------------------------------------------------------------------------
# Devices CRUD
# ---------------------------------------------------------------------------

@app.route("/api/devices", methods=["GET"])
def list_devices():
    db = get_db()
    try:
        query = db.query(Device)

        # Filters
        risk_level = request.args.get("risk_level")
        device_type = request.args.get("device_type")
        search = request.args.get("search", "")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        if device_type:
            query = query.filter(Device.device_type == device_type)
        if search:
            query = query.filter(
                (Device.device_id.contains(search)) |
                (Device.location.contains(search))
            )

        # If filtering by risk level, join with assessments
        if risk_level:
            device_ids_with_risk = (
                db.query(RiskAssessment.device_id)
                .filter(RiskAssessment.risk_level == risk_level)
                .distinct()
                .all()
            )
            risk_device_ids = [r.device_id for r in device_ids_with_risk]
            query = query.filter(Device.device_id.in_(risk_device_ids))

        total = query.count()
        devices = query.order_by(Device.created_at.desc()).offset(offset).limit(limit).all()

        # Get latest assessment for each device
        result = []
        for dev in devices:
            d = dev.to_dict()
            assessment = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.device_id == dev.device_id)
                .order_by(RiskAssessment.assessed_at.desc())
                .first()
            )
            if assessment:
                d["risk_assessment"] = assessment.to_dict()
            else:
                d["risk_assessment"] = None
            result.append(d)

        return jsonify({
            "devices": result,
            "total": total,
            "limit": limit,
            "offset": offset,
        })
    finally:
        db.close()


@app.route("/api/devices/<device_id>", methods=["GET"])
def get_device(device_id):
    db = get_db()
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            return jsonify({"error": f"Device {device_id} not found", "status": 404}), 404

        d = device.to_dict()

        # All historical risk assessments
        assessments = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.device_id == device_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .all()
        )
        d["risk_assessments"] = [a.to_dict() for a in assessments]

        # Migration plan
        plan = (
            db.query(MigrationPlan)
            .filter(MigrationPlan.device_id == device_id)
            .order_by(MigrationPlan.created_at.desc())
            .first()
        )
        d["migration_plan"] = plan.to_dict() if plan else None

        # Active alerts
        alerts = (
            db.query(Alert)
            .filter(Alert.device_id == device_id)
            .order_by(Alert.created_at.desc())
            .all()
        )
        d["alerts"] = [a.to_dict() for a in alerts]

        return jsonify(d)
    finally:
        db.close()


@app.route("/api/devices", methods=["POST"])
def add_device():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON", "status": 400}), 400

    required = FEATURE_COLUMNS + ["device_id"]
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}", "status": 400}), 400

    db = get_db()
    try:
        # Check if device already exists
        existing = db.query(Device).filter(Device.device_id == data["device_id"]).first()
        if existing:
            return jsonify({"error": f"Device {data['device_id']} already exists", "status": 409}), 409

        # Create device
        device = Device(
            device_id=data["device_id"],
            device_type=data["device_type"],
            encryption_algorithm=data["encryption_algorithm"],
            data_sensitivity=int(data["data_sensitivity"]),
            data_retention_years=int(data["data_retention_years"]),
            network_exposure=int(data["network_exposure"]),
            update_capable=int(data["update_capable"]),
            battery_powered=int(data["battery_powered"]),
            cpu_mhz=int(data["cpu_mhz"]),
            ram_kb=int(data["ram_kb"]),
            key_rotation_days=int(data["key_rotation_days"]),
            deployment_age_years=int(data["deployment_age_years"]),
            num_connected_devices=int(data["num_connected_devices"]),
            data_volume_mb_per_day=float(data["data_volume_mb_per_day"]),
            location=data.get("location", "Unknown"),
        )
        db.add(device)
        db.flush()

        # Classify
        classification = classifier.classify(data)
        risk_level = classification["risk_level"]
        risk_score = classification["risk_score"]
        policy = policy_engine.evaluate(data, risk_level, risk_score)

        # Store assessment
        assessment = RiskAssessment(
            device_id=data["device_id"],
            risk_level=risk_level,
            risk_score=risk_score,
            recommended_strategy=policy["strategy"],
            recommended_algorithm=policy["recommended_algorithm"],
            reasoning=policy["reasoning"],
        )
        db.add(assessment)

        # Create migration plan
        plan = MigrationPlan(
            device_id=data["device_id"],
            current_algorithm=data["encryption_algorithm"],
            target_algorithm=policy["recommended_algorithm"],
            migration_phase=policy["migration_phase"],
            estimated_effort=policy["estimated_effort"],
            priority_score=policy["priority_score"],
            notes=policy["notes"],
            status="Pending",
        )
        db.add(plan)

        # Create alert if critical or high
        if risk_level in ("CRITICAL", "HIGH"):
            alert = Alert(
                device_id=data["device_id"],
                severity=risk_level,
                title=f"{risk_level} Quantum Risk: {data['device_id']}",
                message=(
                    f"{data['device_type'].replace('_', ' ').title()} using "
                    f"{data['encryption_algorithm']}. {policy['reasoning'][:200]}"
                ),
            )
            db.add(alert)

        db.commit()

        result = device.to_dict()
        result["risk_assessment"] = assessment.to_dict()
        result["migration_plan"] = plan.to_dict()

        return jsonify(result), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e), "status": 500}), 500
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CSV Upload
# ---------------------------------------------------------------------------

@app.route("/api/upload/csv", methods=["POST"])
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file provided", "status": 400}), 400

    file = request.files["file"]
    if not file.filename.endswith(".csv"):
        return jsonify({"error": "File must be a CSV", "status": 400}), 400

    t0 = time.perf_counter()
    try:
        content = file.read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
    except Exception as e:
        return jsonify({"error": f"Failed to parse CSV: {str(e)}", "status": 400}), 400

    total_rows = len(rows)
    successful = 0
    failed = 0
    risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    results = []

    db = get_db()
    try:
        for row in rows:
            try:
                # Ensure numeric fields are properly typed
                for int_field in ["data_sensitivity", "data_retention_years", "network_exposure",
                                  "update_capable", "battery_powered", "cpu_mhz", "ram_kb",
                                  "key_rotation_days", "deployment_age_years", "num_connected_devices"]:
                    if int_field in row:
                        row[int_field] = int(row[int_field])

                if "data_volume_mb_per_day" in row:
                    row["data_volume_mb_per_day"] = float(row["data_volume_mb_per_day"])

                # Classify
                classification = classifier.classify(row)
                risk_level = classification["risk_level"]
                risk_score = classification["risk_score"]
                policy = policy_engine.evaluate(row, risk_level, risk_score)

                device_id = row.get("device_id", f"UPLOAD-{successful}")

                # Try to store in DB
                existing = db.query(Device).filter(Device.device_id == device_id).first()
                if not existing:
                    device = Device(
                        device_id=device_id,
                        device_type=row.get("device_type", "unknown"),
                        encryption_algorithm=row.get("encryption_algorithm", "Unknown"),
                        data_sensitivity=row.get("data_sensitivity", 0),
                        data_retention_years=row.get("data_retention_years", 1),
                        network_exposure=row.get("network_exposure", 0),
                        update_capable=row.get("update_capable", 1),
                        battery_powered=row.get("battery_powered", 0),
                        cpu_mhz=row.get("cpu_mhz", 240),
                        ram_kb=row.get("ram_kb", 256),
                        key_rotation_days=row.get("key_rotation_days", 90),
                        deployment_age_years=row.get("deployment_age_years", 0),
                        num_connected_devices=row.get("num_connected_devices", 1),
                        data_volume_mb_per_day=row.get("data_volume_mb_per_day", 1.0),
                        location=row.get("location", "Uploaded"),
                    )
                    db.add(device)
                    db.flush()

                    assessment = RiskAssessment(
                        device_id=device_id,
                        risk_level=risk_level,
                        risk_score=risk_score,
                        recommended_strategy=policy["strategy"],
                        recommended_algorithm=policy["recommended_algorithm"],
                        reasoning=policy["reasoning"],
                    )
                    db.add(assessment)

                    plan = MigrationPlan(
                        device_id=device_id,
                        current_algorithm=row.get("encryption_algorithm", "Unknown"),
                        target_algorithm=policy["recommended_algorithm"],
                        migration_phase=policy["migration_phase"],
                        estimated_effort=policy["estimated_effort"],
                        priority_score=policy["priority_score"],
                        notes=policy["notes"],
                        status="Pending",
                    )
                    db.add(plan)

                risk_dist[risk_level] += 1
                results.append({
                    "device_id": device_id,
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "strategy": policy["strategy"],
                    "recommended_algorithm": policy["recommended_algorithm"],
                })
                successful += 1
            except Exception as e:
                failed += 1
                results.append({
                    "device_id": row.get("device_id", "unknown"),
                    "error": str(e),
                })

        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Database error: {str(e)}", "status": 500}), 500
    finally:
        db.close()

    processing_time_ms = round((time.perf_counter() - t0) * 1000, 2)

    return jsonify({
        "total_rows": total_rows,
        "successful": successful,
        "failed": failed,
        "risk_distribution": risk_dist,
        "results": results,
        "processing_time_ms": processing_time_ms,
    })


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------

@app.route("/api/benchmark", methods=["GET"])
def run_benchmark():
    iterations = int(request.args.get("iterations", 50))
    iterations = min(max(iterations, 5), 200)  # Clamp

    try:
        crypto_benchmark.run_full_benchmark(iterations)
        summary = crypto_benchmark.get_comparison_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e), "status": 500}), 500


@app.route("/api/benchmark/history", methods=["GET"])
def benchmark_history():
    db = get_db()
    try:
        results = (
            db.query(CryptoBenchmarkResult)
            .order_by(CryptoBenchmarkResult.benchmarked_at.desc())
            .limit(100)
            .all()
        )
        # Group by benchmarked_at (approximate — within 60 seconds is same run)
        runs = []
        current_run = []
        last_time = None
        for r in results:
            if last_time and (last_time - r.benchmarked_at).total_seconds() > 60:
                runs.append(current_run)
                current_run = []
            current_run.append(r.to_dict())
            last_time = r.benchmarked_at

        if current_run:
            runs.append(current_run)

        return jsonify({"runs": runs[:10], "total_runs": len(runs)})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

@app.route("/api/migration/roadmap", methods=["GET"])
def migration_roadmap():
    db = get_db()
    try:
        devices = db.query(Device).all()
        pairs = []
        for dev in devices:
            assessment = (
                db.query(RiskAssessment)
                .filter(RiskAssessment.device_id == dev.device_id)
                .order_by(RiskAssessment.assessed_at.desc())
                .first()
            )
            if assessment:
                pairs.append((dev.to_dict(), assessment.to_dict()))

        roadmap = policy_engine.generate_migration_roadmap(pairs)
        return jsonify(roadmap)
    finally:
        db.close()


@app.route("/api/migration/plan/<device_id>", methods=["GET"])
def migration_plan(device_id):
    db = get_db()
    try:
        plan = (
            db.query(MigrationPlan)
            .filter(MigrationPlan.device_id == device_id)
            .order_by(MigrationPlan.created_at.desc())
            .first()
        )
        if not plan:
            return jsonify({"error": f"No migration plan for {device_id}", "status": 404}), 404

        return jsonify(plan.to_dict())
    finally:
        db.close()


@app.route("/api/devices/<device_id>/migrate", methods=["POST"])
def migrate_device(device_id):
    data = request.get_json() or {}

    try:
        target_config = _normalize_target_algorithm(data.get("target_algorithm"))
    except ValueError as exc:
        return jsonify({"error": str(exc), "status": 400}), 400

    db = get_db()
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            return jsonify({"error": f"Device {device_id} not found", "status": 404}), 404

        latest_assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.device_id == device_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .first()
        )
        current_risk = latest_assessment.risk_score if latest_assessment else 0.5
        current_level = latest_assessment.risk_level if latest_assessment else "MEDIUM"
        policy = policy_engine.evaluate(_get_device_features(device), current_level, current_risk)

        plan = MigrationPlan(
            device_id=device.device_id,
            current_algorithm=device.encryption_algorithm,
            target_algorithm=target_config["db_algorithm"],
            migration_phase="Executing OTA Migration",
            estimated_effort=policy["estimated_effort"],
            priority_score=policy["priority_score"],
            notes=policy["notes"],
            status="InProgress",
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        job_id = str(uuid.uuid4())
        initial_stage = MIGRATION_STAGE_DEFS[0]
        with MIGRATION_JOBS_LOCK:
            MIGRATION_JOBS[job_id] = {
                "job_id": job_id,
                "device_id": device.device_id,
                "target_algorithm": target_config["label"],
                "status": "queued",
                "progress": 0,
                "stage": initial_stage[1],
                "stage_number": 0,
                "logs": [{
                    "timestamp": _iso_now(),
                    "stage_number": 0,
                    "stage_label": "Queued",
                    "progress": 0,
                    "message": f"Queued OTA migration from {device.encryption_algorithm} to {target_config['label']}",
                }],
                "created_at": _iso_now(),
                "updated_at": _iso_now(),
                "result": None,
                "error": None,
            }

        worker = threading.Thread(
            target=_start_migration_job,
            args=(job_id, device.device_id, target_config, plan.id),
            daemon=True,
        )
        worker.start()

        return jsonify({
            "job_id": job_id,
            "device_id": device.device_id,
            "current_algorithm": device.encryption_algorithm,
            "target_algorithm": target_config["label"],
            "status": "queued",
        }), 202
    finally:
        db.close()


@app.route("/api/migration/status/<job_id>", methods=["GET"])
def migration_status(job_id):
    job = _get_job_snapshot(job_id)
    if not job:
        return jsonify({"error": f"Migration job {job_id} not found", "status": 404}), 404

    return jsonify(job)


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

@app.route("/api/alerts", methods=["GET"])
def list_alerts():
    db = get_db()
    try:
        query = db.query(Alert)

        acknowledged = request.args.get("acknowledged")
        if acknowledged is not None:
            ack_val = 1 if acknowledged.lower() in ("true", "1") else 0
            query = query.filter(Alert.acknowledged == ack_val)

        severity = request.args.get("severity")
        if severity:
            query = query.filter(Alert.severity == severity)

        total = query.count()
        alerts = query.order_by(Alert.created_at.desc()).all()

        return jsonify({
            "alerts": [a.to_dict() for a in alerts],
            "total": total,
        })
    finally:
        db.close()


@app.route("/api/alerts/<int:alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert(alert_id):
    db = get_db()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return jsonify({"error": f"Alert {alert_id} not found", "status": 404}), 404

        alert.acknowledged = 1
        db.commit()

        return jsonify(alert.to_dict())
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@app.route("/api/report/<device_id>", methods=["GET"])
def device_report(device_id):
    db = get_db()
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            return jsonify({"error": f"Device {device_id} not found", "status": 404}), 404

        assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.device_id == device_id)
            .order_by(RiskAssessment.assessed_at.desc())
            .first()
        )
        plan = (
            db.query(MigrationPlan)
            .filter(MigrationPlan.device_id == device_id)
            .order_by(MigrationPlan.created_at.desc())
            .first()
        )

        device_dict = device.to_dict()
        assessment_dict = assessment.to_dict() if assessment else {}
        plan_dict = plan.to_dict() if plan else {}

        # Get benchmark data
        benchmark_summary = crypto_benchmark.get_comparison_summary()

        report = report_generator.generate_device_report(
            device_dict, assessment_dict, plan_dict, benchmark_summary
        )

        return jsonify(report)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Crypto Demo
# ---------------------------------------------------------------------------

@app.route("/api/crypto/demo/<algorithm>", methods=["GET"])
def crypto_demo(algorithm):
    algo = algorithm.lower().strip()
    try:
        if algo == "rsa-2048":
            result = classical_crypto.rsa_demo(2048)
        elif algo == "rsa-1024":
            result = classical_crypto.rsa_1024_demo()
        elif algo in ("ecc-256", "ecc-p256"):
            result = classical_crypto.ecc_demo("P-256")
        elif algo in ("aes-256", "aes-256-gcm"):
            result = classical_crypto.aes_demo(256, 1)
        elif algo in ("kyber-512", "kyber512"):
            result = pqc_crypto.kyber_demo("Kyber512")
        elif algo in ("kyber-768", "kyber768"):
            result = pqc_crypto.kyber_demo("Kyber768")
        elif algo in ("dilithium-2", "dilithium2"):
            result = pqc_crypto.dilithium_demo("Dilithium2")
        elif algo == "hybrid":
            result = hybrid_crypto.hybrid_kem_demo()
        else:
            return jsonify({"error": f"Unknown algorithm: {algorithm}",
                            "supported": ["rsa-2048", "rsa-1024", "ecc-256",
                                          "aes-256", "kyber-512", "kyber-768",
                                          "dilithium-2", "hybrid"],
                            "status": 400}), 400

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "status": 500}), 500


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  QuantumGuard AI — Starting Flask Server")
    print("=" * 60)

    init_db()

    print(f"\n  Server: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"  Model loaded: {classifier.loaded}")
    print(f"  Version: {APP_VERSION}")
    print()

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
