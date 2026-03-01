"""
QuantumGuard AI — Configuration Constants
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database
DATABASE_PATH = os.path.join(BASE_DIR, "quantumguard.db")
DATABASE_URI = f"sqlite:///{DATABASE_PATH}"

# ML Model paths
ML_DIR = os.path.join(BASE_DIR, "ml")
DATASET_PATH = os.path.join(ML_DIR, "iot_dataset.csv")
MODEL_PATH = os.path.join(ML_DIR, "quantumguard_model.pkl")
PREPROCESSOR_PATH = os.path.join(ML_DIR, "preprocessor.pkl")
MODEL_METADATA_PATH = os.path.join(ML_DIR, "model_metadata.json")

# Flask
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
FLASK_DEBUG = True

# App
APP_VERSION = "1.0.0"

# Feature columns used by the ML model
FEATURE_COLUMNS = [
    "device_type",
    "encryption_algorithm",
    "data_sensitivity",
    "data_retention_years",
    "network_exposure",
    "update_capable",
    "battery_powered",
    "cpu_mhz",
    "ram_kb",
    "key_rotation_days",
    "deployment_age_years",
    "num_connected_devices",
    "data_volume_mb_per_day",
]

# Categorical features (for encoding)
CATEGORICAL_FEATURES = ["device_type", "encryption_algorithm"]

# Ordinal features (already numeric, keep as-is)
ORDINAL_FEATURES = ["data_sensitivity"]

# Numeric features (for scaling)
NUMERIC_FEATURES = [
    "data_retention_years",
    "network_exposure",
    "update_capable",
    "battery_powered",
    "cpu_mhz",
    "ram_kb",
    "key_rotation_days",
    "deployment_age_years",
    "num_connected_devices",
    "data_volume_mb_per_day",
]

# Risk labels
RISK_LABELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

# Device types
DEVICE_TYPES = [
    "environmental_sensor",
    "medical_wearable",
    "industrial_controller",
    "smart_home",
    "energy_meter",
    "security_camera",
    "autonomous_vehicle_sensor",
    "water_treatment_sensor",
]

# Encryption algorithms
ENCRYPTION_ALGORITHMS = [
    "RSA-1024",
    "RSA-2048",
    "ECC-256",
    "ECC-384",
    "AES-128",
    "AES-256",
    "3DES",
    "ChaCha20",
    "Kyber-512",
    "Kyber-768",
    "HYBRID-ECC-Kyber",
]

# CPU options
CPU_OPTIONS = [80, 160, 240, 1000, 1200, 1500, 2000, 3000]

# RAM options
RAM_OPTIONS = [64, 128, 256, 512, 2048, 4096, 8192, 16384]
