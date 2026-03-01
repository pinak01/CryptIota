"""
QuantumGuard AI — Synthetic IoT Dataset Generator
Generates 12,000 rows of IoT device profiles with deterministic risk labeling.
"""
import os
import sys
import numpy as np
import pandas as pd

# Ensure we can import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    DEVICE_TYPES, ENCRYPTION_ALGORITHMS, CPU_OPTIONS, RAM_OPTIONS, DATASET_PATH
)

SEED = 42
NUM_ROWS = 12000
NOISE_FRACTION = 0.05  # 5% deliberate noise


# ---------------------------------------------------------------------------
# Per-device-type probability distributions
# ---------------------------------------------------------------------------

DEVICE_TYPE_PROFILES = {
    "environmental_sensor": {
        "algos": ["AES-128", "AES-256", "ChaCha20", "ECC-256", "RSA-2048"],
        "algo_weights": [0.25, 0.30, 0.15, 0.15, 0.15],
        "sensitivity_weights": [0.30, 0.35, 0.25, 0.08, 0.02],
        "network_exposure_prob": 0.3,
        "update_capable_prob": 0.6,
        "battery_powered_prob": 0.7,
        "cpu_weights": [0.30, 0.25, 0.20, 0.10, 0.05, 0.05, 0.03, 0.02],
        "ram_weights": [0.20, 0.25, 0.25, 0.15, 0.08, 0.04, 0.02, 0.01],
        "retention_range": (1, 5),
        "age_range": (0, 10),
        "connected_range": (1, 50),
        "volume_range": (0.1, 10.0),
    },
    "medical_wearable": {
        "algos": ["RSA-1024", "RSA-2048", "ECC-256", "ECC-384", "AES-256", "Kyber-512", "HYBRID-ECC-Kyber"],
        "algo_weights": [0.10, 0.20, 0.15, 0.10, 0.20, 0.15, 0.10],
        "sensitivity_weights": [0.02, 0.05, 0.15, 0.40, 0.38],
        "network_exposure_prob": 0.7,
        "update_capable_prob": 0.5,
        "battery_powered_prob": 0.9,
        "cpu_weights": [0.10, 0.20, 0.25, 0.15, 0.10, 0.10, 0.05, 0.05],
        "ram_weights": [0.05, 0.10, 0.20, 0.25, 0.20, 0.10, 0.05, 0.05],
        "retention_range": (5, 25),
        "age_range": (0, 8),
        "connected_range": (1, 20),
        "volume_range": (0.5, 50.0),
    },
    "industrial_controller": {
        "algos": ["RSA-2048", "ECC-256", "ECC-384", "AES-128", "AES-256", "3DES", "Kyber-768"],
        "algo_weights": [0.15, 0.15, 0.10, 0.15, 0.20, 0.10, 0.15],
        "sensitivity_weights": [0.05, 0.10, 0.30, 0.35, 0.20],
        "network_exposure_prob": 0.4,
        "update_capable_prob": 0.3,
        "battery_powered_prob": 0.1,
        "cpu_weights": [0.02, 0.05, 0.08, 0.15, 0.20, 0.20, 0.15, 0.15],
        "ram_weights": [0.02, 0.03, 0.05, 0.10, 0.20, 0.25, 0.20, 0.15],
        "retention_range": (3, 20),
        "age_range": (1, 15),
        "connected_range": (5, 200),
        "volume_range": (1.0, 500.0),
    },
    "smart_home": {
        "algos": ["AES-128", "AES-256", "ChaCha20", "ECC-256", "RSA-2048", "Kyber-512"],
        "algo_weights": [0.20, 0.25, 0.15, 0.15, 0.15, 0.10],
        "sensitivity_weights": [0.20, 0.30, 0.30, 0.15, 0.05],
        "network_exposure_prob": 0.8,
        "update_capable_prob": 0.7,
        "battery_powered_prob": 0.5,
        "cpu_weights": [0.15, 0.20, 0.25, 0.15, 0.10, 0.05, 0.05, 0.05],
        "ram_weights": [0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.05, 0.05],
        "retention_range": (1, 5),
        "age_range": (0, 7),
        "connected_range": (5, 100),
        "volume_range": (0.1, 50.0),
    },
    "energy_meter": {
        "algos": ["RSA-2048", "ECC-256", "ECC-384", "AES-128", "AES-256", "3DES", "Kyber-768"],
        "algo_weights": [0.15, 0.20, 0.10, 0.15, 0.20, 0.05, 0.15],
        "sensitivity_weights": [0.05, 0.15, 0.35, 0.30, 0.15],
        "network_exposure_prob": 0.6,
        "update_capable_prob": 0.5,
        "battery_powered_prob": 0.2,
        "cpu_weights": [0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.05],
        "ram_weights": [0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.05],
        "retention_range": (3, 15),
        "age_range": (1, 12),
        "connected_range": (10, 500),
        "volume_range": (1.0, 200.0),
    },
    "security_camera": {
        "algos": ["RSA-1024", "RSA-2048", "ECC-256", "AES-128", "AES-256", "ChaCha20"],
        "algo_weights": [0.10, 0.20, 0.15, 0.15, 0.25, 0.15],
        "sensitivity_weights": [0.05, 0.15, 0.35, 0.30, 0.15],
        "network_exposure_prob": 0.9,
        "update_capable_prob": 0.4,
        "battery_powered_prob": 0.1,
        "cpu_weights": [0.03, 0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.12],
        "ram_weights": [0.02, 0.05, 0.08, 0.15, 0.20, 0.25, 0.15, 0.10],
        "retention_range": (1, 10),
        "age_range": (0, 10),
        "connected_range": (1, 100),
        "volume_range": (10.0, 1000.0),
    },
    "autonomous_vehicle_sensor": {
        "algos": ["RSA-2048", "ECC-256", "ECC-384", "AES-256", "Kyber-512", "Kyber-768", "HYBRID-ECC-Kyber"],
        "algo_weights": [0.10, 0.15, 0.10, 0.20, 0.15, 0.15, 0.15],
        "sensitivity_weights": [0.02, 0.05, 0.15, 0.38, 0.40],
        "network_exposure_prob": 0.6,
        "update_capable_prob": 0.8,
        "battery_powered_prob": 0.3,
        "cpu_weights": [0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.30, 0.34],
        "ram_weights": [0.01, 0.02, 0.03, 0.05, 0.10, 0.15, 0.30, 0.34],
        "retention_range": (5, 20),
        "age_range": (0, 5),
        "connected_range": (10, 300),
        "volume_range": (50.0, 1000.0),
    },
    "water_treatment_sensor": {
        "algos": ["RSA-2048", "ECC-256", "AES-128", "AES-256", "3DES", "Kyber-512"],
        "algo_weights": [0.15, 0.15, 0.15, 0.25, 0.10, 0.20],
        "sensitivity_weights": [0.05, 0.15, 0.30, 0.30, 0.20],
        "network_exposure_prob": 0.3,
        "update_capable_prob": 0.4,
        "battery_powered_prob": 0.2,
        "cpu_weights": [0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.05],
        "ram_weights": [0.05, 0.10, 0.15, 0.20, 0.20, 0.15, 0.10, 0.05],
        "retention_range": (3, 15),
        "age_range": (1, 12),
        "connected_range": (5, 100),
        "volume_range": (1.0, 100.0),
    },
}


# ---------------------------------------------------------------------------
# Risk labeling oracle
# ---------------------------------------------------------------------------

def label_risk(row: dict) -> str:
    """Apply deterministic risk-labeling rules (ground truth oracle)."""
    algo = row["encryption_algorithm"]
    sens = row["data_sensitivity"]
    ret = row["data_retention_years"]
    dtype = row["device_type"]
    net = row["network_exposure"]
    upd = row["update_capable"]

    pqc_safe = {"AES-256", "Kyber-512", "Kyber-768", "HYBRID-ECC-Kyber"}

    # --- CRITICAL ---
    if algo in ("RSA-1024", "3DES") and sens >= 2:
        return "CRITICAL"
    if algo in ("RSA-2048", "ECC-256") and ret > 10 and sens >= 3:
        return "CRITICAL"
    if dtype in ("medical_wearable", "autonomous_vehicle_sensor") and algo not in pqc_safe and sens >= 3:
        return "CRITICAL"

    # --- HIGH ---
    if algo in ("RSA-2048", "ECC-256", "ECC-384") and ret > 5 and sens >= 2:
        return "HIGH"
    if algo == "AES-128" and sens >= 3:
        return "HIGH"
    if upd == 0 and algo in ("RSA-1024", "RSA-2048", "3DES"):
        return "HIGH"
    if net == 1 and algo in ("RSA-1024", "3DES"):
        return "HIGH"

    # --- MEDIUM ---
    if algo in ("RSA-2048", "ECC-256") and ret <= 5:
        return "MEDIUM"
    if algo == "AES-128" and sens <= 2:
        return "MEDIUM"
    if algo == "ChaCha20" and sens >= 2:
        return "MEDIUM"
    if row["deployment_age_years"] > 8 and upd == 1:
        return "MEDIUM"

    # --- LOW ---
    return "LOW"


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def generate_dataset() -> pd.DataFrame:
    """Generate synthetic IoT device dataset with 12,000 rows."""
    rng = np.random.default_rng(SEED)
    rows = []

    rows_per_type = NUM_ROWS // len(DEVICE_TYPES)  # 1500 per type

    for dtype in DEVICE_TYPES:
        profile = DEVICE_TYPE_PROFILES[dtype]
        for i in range(rows_per_type):
            algo = rng.choice(profile["algos"], p=profile["algo_weights"])
            sens = int(rng.choice([0, 1, 2, 3, 4], p=profile["sensitivity_weights"]))
            ret_lo, ret_hi = profile["retention_range"]
            retention = int(rng.integers(ret_lo, ret_hi + 1))
            net_exp = int(rng.random() < profile["network_exposure_prob"])
            upd_cap = int(rng.random() < profile["update_capable_prob"])
            bat_pow = int(rng.random() < profile["battery_powered_prob"])
            cpu = int(rng.choice(CPU_OPTIONS, p=profile["cpu_weights"]))
            ram = int(rng.choice(RAM_OPTIONS, p=profile["ram_weights"]))
            age_lo, age_hi = profile["age_range"]
            age = int(rng.integers(age_lo, age_hi + 1))
            conn_lo, conn_hi = profile["connected_range"]
            connected = int(rng.integers(conn_lo, conn_hi + 1))
            vol_lo, vol_hi = profile["volume_range"]
            volume = round(float(rng.uniform(vol_lo, vol_hi)), 2)
            key_rot = int(rng.integers(1, 366))

            row = {
                "device_id": f"DEV_{len(rows):05d}",
                "device_type": dtype,
                "encryption_algorithm": algo,
                "data_sensitivity": sens,
                "data_retention_years": retention,
                "network_exposure": net_exp,
                "update_capable": upd_cap,
                "battery_powered": bat_pow,
                "cpu_mhz": cpu,
                "ram_kb": ram,
                "key_rotation_days": key_rot,
                "deployment_age_years": age,
                "num_connected_devices": connected,
                "data_volume_mb_per_day": volume,
            }
            rows.append(row)

    df = pd.DataFrame(rows)

    # Apply risk labels
    df["risk_label"] = df.apply(lambda r: label_risk(r.to_dict()), axis=1)

    # Add 5% noise — randomly flip some features to stress-test model
    noise_count = int(len(df) * NOISE_FRACTION)
    noise_indices = rng.choice(len(df), size=noise_count, replace=False)
    for idx in noise_indices:
        # Randomly swap the encryption algorithm to a different one
        current_algo = df.at[idx, "encryption_algorithm"]
        alternatives = [a for a in ENCRYPTION_ALGORITHMS if a != current_algo]
        df.at[idx, "encryption_algorithm"] = rng.choice(alternatives)
        # Flip network exposure
        df.at[idx, "network_exposure"] = 1 - df.at[idx, "network_exposure"]

    # Re-label after noise (labels stay consistent with noisy features)
    df["risk_label"] = df.apply(lambda r: label_risk(r.to_dict()), axis=1)

    return df


# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  QuantumGuard AI — Synthetic Dataset Generator")
    print("=" * 60)

    df = generate_dataset()

    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    df.to_csv(DATASET_PATH, index=False)
    print(f"\n[✓] Dataset saved to: {DATASET_PATH}")
    print(f"[✓] Total rows: {len(df)}")

    print("\nClass Distribution:")
    print("-" * 30)
    dist = df["risk_label"].value_counts()
    for label in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        count = dist.get(label, 0)
        pct = count / len(df) * 100
        print(f"  {label:10s}: {count:5d}  ({pct:.1f}%)")

    print("\nDevice Type Distribution:")
    print("-" * 30)
    for dtype in sorted(df["device_type"].unique()):
        count = len(df[df["device_type"] == dtype])
        print(f"  {dtype:30s}: {count}")

    print("\n[✓] Dataset generation complete!")


if __name__ == "__main__":
    main()
