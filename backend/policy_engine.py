"""
QuantumGuard AI — Migration Policy Engine
Maps risk levels to cryptographic migration strategies with human-readable reasoning.
"""


class MigrationPolicyEngine:
    """Maps risk assessment results to actionable migration strategies."""

    STRATEGY_MAP = {
        "CRITICAL": {
            "strategy": "PostQuantum",
            "algorithm": "Kyber-512 + Dilithium-2 + AES-256-GCM",
            "phase": "Immediate",
            "effort": "High",
            "timeline": "0–3 months",
        },
        "HIGH": {
            "strategy": "Hybrid",
            "algorithm": "ECDH + Kyber-512 + AES-256-GCM (Hybrid)",
            "phase": "ShortTerm",
            "effort": "Medium",
            "timeline": "3–12 months",
        },
        "MEDIUM": {
            "strategy": "Hybrid",
            "algorithm": "AES-256-GCM + Plan Kyber Migration",
            "phase": "LongTerm",
            "effort": "Low",
            "timeline": "12–24 months",
        },
        "LOW": {
            "strategy": "Classical",
            "algorithm": "AES-256-GCM (monitor for changes)",
            "phase": "Monitor",
            "effort": "Low",
            "timeline": "No immediate action",
        },
    }

    # Device type risk multipliers for priority scoring
    DEVICE_TYPE_WEIGHTS = {
        "medical_wearable": 1.5,
        "autonomous_vehicle_sensor": 1.4,
        "industrial_controller": 1.3,
        "water_treatment_sensor": 1.2,
        "security_camera": 1.1,
        "energy_meter": 1.1,
        "smart_home": 1.0,
        "environmental_sensor": 0.9,
    }

    def evaluate(self, device_data: dict, risk_level: str, risk_score: float) -> dict:
        """Return a complete policy recommendation for a device.

        Args:
            device_data: dict with device attributes
            risk_level: one of LOW/MEDIUM/HIGH/CRITICAL
            risk_score: float 0.0–1.0

        Returns:
            dict with strategy, algorithm, reasoning, priority_score, etc.
        """
        strategy_info = self.STRATEGY_MAP.get(risk_level, self.STRATEGY_MAP["LOW"])

        device_type = device_data.get("device_type", "unknown")
        algo = device_data.get("encryption_algorithm", "Unknown")
        retention = device_data.get("data_retention_years", 0)
        sensitivity = device_data.get("data_sensitivity", 0)
        net_exp = device_data.get("network_exposure", 0)
        update_cap = device_data.get("update_capable", 1)

        # Priority score calculation
        type_weight = self.DEVICE_TYPE_WEIGHTS.get(device_type, 1.0)
        base_priority = risk_score * type_weight

        # Boost for internet-facing devices
        if net_exp == 1:
            base_priority *= 1.1

        # Boost for devices that can't be updated
        if update_cap == 0:
            base_priority *= 1.15

        # Boost for long retention periods
        if retention > 10:
            base_priority *= 1.1

        priority_score = min(round(base_priority, 4), 1.0)

        # Generate human-readable reasoning
        reasoning = self._generate_reasoning(
            device_type, algo, retention, sensitivity,
            net_exp, update_cap, risk_level, strategy_info
        )

        # Determine cost category
        cost_map = {"High": "High", "Medium": "Medium", "Low": "Low"}
        cost = cost_map.get(strategy_info["effort"], "Low")

        # Special notes
        notes = self._generate_notes(device_data, risk_level)

        return {
            "strategy": strategy_info["strategy"],
            "recommended_algorithm": strategy_info["algorithm"],
            "migration_phase": strategy_info["phase"],
            "timeline": strategy_info["timeline"],
            "estimated_effort": strategy_info["effort"],
            "priority_score": priority_score,
            "reasoning": reasoning,
            "estimated_cost_category": cost,
            "notes": notes,
        }

    def _generate_reasoning(self, device_type, algo, retention, sensitivity,
                            net_exp, update_cap, risk_level, strategy_info):
        """Generate a 2–3 sentence human-readable explanation."""
        sensitivity_labels = {
            0: "public", 1: "internal", 2: "confidential",
            3: "sensitive", 4: "critical"
        }
        sens_label = sensitivity_labels.get(sensitivity, "unknown")

        type_display = device_type.replace("_", " ").title()

        parts = []

        if risk_level == "CRITICAL":
            parts.append(
                f"This {type_display} uses {algo} with {sens_label} data "
                f"and {retention}-year retention, placing it well within the "
                f"quantum threat exposure window."
            )
            parts.append(
                f"Immediate migration to {strategy_info['algorithm']} is "
                f"strongly recommended within {strategy_info['timeline']}."
            )
            if not update_cap:
                parts.append(
                    "Note: this device cannot be updated remotely — "
                    "physical intervention may be required."
                )
        elif risk_level == "HIGH":
            parts.append(
                f"This {type_display} running {algo} handles {sens_label} data "
                f"with {retention}-year retention requirements."
            )
            parts.append(
                f"A hybrid migration strategy ({strategy_info['algorithm']}) "
                f"should be planned within {strategy_info['timeline']} "
                f"to ensure quantum resistance before cryptographically relevant "
                f"quantum computers emerge."
            )
        elif risk_level == "MEDIUM":
            parts.append(
                f"This {type_display} uses {algo} for {sens_label} data. "
                f"While not immediately vulnerable, quantum computing advances "
                f"could pose risks within the {retention}-year data lifecycle."
            )
            parts.append(
                f"Plan migration to {strategy_info['algorithm']} within "
                f"{strategy_info['timeline']}."
            )
        else:  # LOW
            parts.append(
                f"This {type_display} uses {algo} with {sens_label} data and "
                f"{retention}-year retention. Current encryption satisfies "
                f"quantum-resistance requirements."
            )
            parts.append(
                "Continue monitoring for changes in quantum computing "
                "threat landscape and NIST guidelines."
            )

        if net_exp == 1 and risk_level in ("CRITICAL", "HIGH"):
            parts.append(
                "The device is internet-facing, increasing its exposure "
                "to harvest-now-decrypt-later attacks."
            )

        return " ".join(parts)

    def _generate_notes(self, device_data, risk_level):
        """Generate special consideration notes."""
        notes_list = []
        device_type = device_data.get("device_type", "")
        battery = device_data.get("battery_powered", 0)
        cpu = device_data.get("cpu_mhz", 0)
        ram = device_data.get("ram_kb", 0)

        if battery and risk_level in ("CRITICAL", "HIGH"):
            notes_list.append(
                "Battery-powered device — PQC implementation must be "
                "optimized for power consumption."
            )

        if cpu < 240 and risk_level in ("CRITICAL", "HIGH"):
            notes_list.append(
                f"Low CPU ({cpu} MHz) — may require hardware upgrade "
                f"or lightweight PQC variant."
            )

        if ram < 256 and risk_level in ("CRITICAL", "HIGH"):
            notes_list.append(
                f"Limited RAM ({ram} KB) — Kyber-512 requires ~1.6KB "
                f"for keys; implementation feasibility should be assessed."
            )

        if device_type == "medical_wearable":
            notes_list.append(
                "Medical device — regulatory compliance (HIPAA/GDPR) "
                "must be maintained during migration."
            )

        if device_type == "autonomous_vehicle_sensor":
            notes_list.append(
                "Safety-critical system — migration must not interrupt "
                "real-time sensor data processing."
            )

        if device_type == "industrial_controller":
            notes_list.append(
                "Industrial system — schedule migration during "
                "maintenance windows to avoid production disruption."
            )

        return " | ".join(notes_list) if notes_list else "Standard migration procedure."

    def generate_migration_roadmap(self, devices_with_risks: list) -> dict:
        """Generate an ordered migration plan grouped by phase.

        Args:
            devices_with_risks: list of (device_dict, risk_assessment_dict) tuples

        Returns:
            dict with phase groups and per-device recommendations,
            sorted by priority_score descending within each phase.
        """
        roadmap = {
            "Immediate": [],
            "ShortTerm": [],
            "LongTerm": [],
            "Monitor": [],
            "summary": {
                "total_devices": 0,
                "immediate_count": 0,
                "shortterm_count": 0,
                "longterm_count": 0,
                "monitor_count": 0,
            },
        }

        all_plans = []
        for device_data, risk_assessment in devices_with_risks:
            risk_level = risk_assessment.get("risk_level", "LOW")
            risk_score = risk_assessment.get("risk_score", 0.0)

            recommendation = self.evaluate(device_data, risk_level, risk_score)

            plan = {
                "device_id": device_data.get("device_id", "unknown"),
                "device_type": device_data.get("device_type", "unknown"),
                "location": device_data.get("location", "Unknown"),
                "current_algorithm": device_data.get("encryption_algorithm", "Unknown"),
                "target_algorithm": recommendation["recommended_algorithm"],
                "migration_phase": recommendation["migration_phase"],
                "priority_score": recommendation["priority_score"],
                "estimated_effort": recommendation["estimated_effort"],
                "timeline": recommendation["timeline"],
                "strategy": recommendation["strategy"],
                "reasoning": recommendation["reasoning"],
                "notes": recommendation["notes"],
                "risk_level": risk_level,
                "risk_score": risk_score,
            }
            all_plans.append(plan)

        # Sort by priority score descending
        all_plans.sort(key=lambda x: x["priority_score"], reverse=True)

        # Group by phase
        for plan in all_plans:
            phase = plan["migration_phase"]
            if phase in roadmap:
                roadmap[phase].append(plan)

        roadmap["summary"]["total_devices"] = len(all_plans)
        roadmap["summary"]["immediate_count"] = len(roadmap["Immediate"])
        roadmap["summary"]["shortterm_count"] = len(roadmap["ShortTerm"])
        roadmap["summary"]["longterm_count"] = len(roadmap["LongTerm"])
        roadmap["summary"]["monitor_count"] = len(roadmap["Monitor"])

        return roadmap
