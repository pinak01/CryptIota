"""
QuantumGuard AI — Report Generator
Generates JSON migration reports per device (with optional PDF via ReportLab).
"""
import json
from datetime import datetime


class ReportGenerator:
    """Generate comprehensive migration reports for devices."""

    def generate_device_report(self, device: dict, risk_assessment: dict,
                                migration_plan: dict, benchmark_data: dict = None) -> dict:
        """Generate a complete JSON migration report for a single device.

        Args:
            device: device profile dict
            risk_assessment: risk assessment dict
            migration_plan: migration plan dict
            benchmark_data: optional benchmark comparison dict

        Returns:
            Comprehensive report dict
        """
        report = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "report_type": "Device Migration Assessment",
                "version": "1.0",
                "report_id": f"RPT-{device.get('device_id', 'UNKNOWN')}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            },
            "device_profile": {
                "device_id": device.get("device_id"),
                "device_type": device.get("device_type"),
                "location": device.get("location", "Unknown"),
                "current_encryption": device.get("encryption_algorithm"),
                "data_sensitivity": device.get("data_sensitivity"),
                "data_sensitivity_label": self._sensitivity_label(device.get("data_sensitivity", 0)),
                "data_retention_years": device.get("data_retention_years"),
                "network_exposure": "Internet-facing" if device.get("network_exposure") else "Isolated",
                "update_capable": "Yes" if device.get("update_capable") else "No",
                "battery_powered": "Yes" if device.get("battery_powered") else "No",
                "cpu_mhz": device.get("cpu_mhz"),
                "ram_kb": device.get("ram_kb"),
                "deployment_age_years": device.get("deployment_age_years"),
                "num_connected_devices": device.get("num_connected_devices"),
            },
            "risk_assessment": {
                "risk_level": risk_assessment.get("risk_level"),
                "risk_score": risk_assessment.get("risk_score"),
                "confidence_scores": risk_assessment.get("confidence_scores", {}),
                "assessed_at": risk_assessment.get("assessed_at"),
            },
            "migration_recommendation": {
                "current_algorithm": migration_plan.get("current_algorithm"),
                "target_algorithm": migration_plan.get("target_algorithm"),
                "migration_phase": migration_plan.get("migration_phase"),
                "estimated_timeline": migration_plan.get("timeline",
                    self._phase_to_timeline(migration_plan.get("migration_phase", "Monitor"))),
                "estimated_effort": migration_plan.get("estimated_effort"),
                "priority_score": migration_plan.get("priority_score"),
                "strategy": migration_plan.get("strategy"),
                "reasoning": migration_plan.get("reasoning", risk_assessment.get("reasoning", "")),
                "notes": migration_plan.get("notes", ""),
            },
            "migration_steps": self._generate_migration_steps(
                device, risk_assessment, migration_plan
            ),
            "quantum_threat_analysis": {
                "current_algorithm_quantum_safe": self._is_quantum_safe(
                    device.get("encryption_algorithm", "")
                ),
                "harvest_now_decrypt_later_risk": (
                    "HIGH" if device.get("network_exposure") and
                    device.get("data_retention_years", 0) > 5 and
                    not self._is_quantum_safe(device.get("encryption_algorithm", ""))
                    else "LOW"
                ),
                "estimated_years_until_quantum_threat": "5–15 years (expert consensus)",
                "data_exposure_window": f"{device.get('data_retention_years', 0)} years",
            },
        }

        if benchmark_data:
            current_algo = device.get("encryption_algorithm", "")
            target_algo = migration_plan.get("target_algorithm", "")
            report["algorithm_comparison"] = {
                "current": self._find_benchmark(benchmark_data, current_algo),
                "recommended": self._find_benchmark(benchmark_data, target_algo),
            }

        return report

    def _sensitivity_label(self, level):
        labels = {0: "Public", 1: "Internal", 2: "Confidential",
                  3: "Sensitive", 4: "Critical"}
        return labels.get(level, "Unknown")

    def _phase_to_timeline(self, phase):
        timelines = {
            "Immediate": "0–3 months",
            "ShortTerm": "3–12 months",
            "LongTerm": "12–24 months",
            "Monitor": "No immediate action",
        }
        return timelines.get(phase, "TBD")

    def _is_quantum_safe(self, algo):
        safe_algos = {"AES-256", "AES-128", "Kyber-512", "Kyber-768",
                      "Kyber-1024", "HYBRID-ECC-Kyber", "ChaCha20"}
        return algo in safe_algos

    def _find_benchmark(self, benchmark_data, algo_name):
        """Find benchmark data for a specific algorithm."""
        if isinstance(benchmark_data, dict) and "details" in benchmark_data:
            for detail in benchmark_data["details"]:
                if detail.get("algorithm", "").lower() in algo_name.lower():
                    return detail
        return {"note": f"No benchmark data available for {algo_name}"}

    def _generate_migration_steps(self, device, risk_assessment, migration_plan):
        """Generate step-by-step migration instructions."""
        risk_level = risk_assessment.get("risk_level", "LOW")
        device_type = device.get("device_type", "unknown")
        current_algo = device.get("encryption_algorithm", "Unknown")
        target_algo = migration_plan.get("target_algorithm", "Unknown")

        steps = []

        if risk_level in ("CRITICAL", "HIGH"):
            steps.append({
                "step": 1,
                "title": "Inventory & Assessment",
                "description": f"Audit all {device_type.replace('_', ' ')} "
                               f"devices currently using {current_algo}.",
                "estimated_duration": "1–2 weeks",
            })
            steps.append({
                "step": 2,
                "title": "Compatibility Testing",
                "description": f"Test {target_algo} implementation on a "
                               f"representative {device_type.replace('_', ' ')} "
                               f"device in a staging environment.",
                "estimated_duration": "2–4 weeks",
            })
            steps.append({
                "step": 3,
                "title": "Key Generation & Distribution",
                "description": f"Generate new {target_algo} key pairs and "
                               f"distribute securely to all affected devices.",
                "estimated_duration": "1–2 weeks",
            })
            steps.append({
                "step": 4,
                "title": "Parallel Operation",
                "description": "Run both old and new algorithms simultaneously "
                               "to verify correctness and performance.",
                "estimated_duration": "2–4 weeks",
            })
            steps.append({
                "step": 5,
                "title": "Cutover & Validation",
                "description": f"Switch to {target_algo} as primary, deprecate "
                               f"{current_algo}, and validate all connections.",
                "estimated_duration": "1 week",
            })
            steps.append({
                "step": 6,
                "title": "Post-Migration Monitoring",
                "description": "Monitor performance metrics, error rates, and "
                               "security logs for 30 days post-migration.",
                "estimated_duration": "4 weeks",
            })
        elif risk_level == "MEDIUM":
            steps.append({
                "step": 1,
                "title": "Planning",
                "description": f"Add {device_type.replace('_', ' ')} devices "
                               f"to the migration roadmap for {target_algo}.",
                "estimated_duration": "Ongoing",
            })
            steps.append({
                "step": 2,
                "title": "Preparation",
                "description": "Ensure firmware/software supports hybrid or "
                               "PQC algorithms. Plan upgrade path.",
                "estimated_duration": "3–6 months",
            })
            steps.append({
                "step": 3,
                "title": "Staged Migration",
                "description": f"Migrate to {target_algo} during scheduled "
                               f"maintenance windows.",
                "estimated_duration": "6–12 months",
            })
        else:
            steps.append({
                "step": 1,
                "title": "Monitor",
                "description": "Continue monitoring NIST PQC standards and "
                               "quantum computing developments.",
                "estimated_duration": "Ongoing",
            })
            steps.append({
                "step": 2,
                "title": "Review",
                "description": "Reassess risk quarterly as quantum computing "
                               "capabilities advance.",
                "estimated_duration": "Quarterly",
            })

        return steps
