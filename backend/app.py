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
