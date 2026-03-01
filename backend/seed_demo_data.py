"""
QuantumGuard AI — Demo Data Seeder
Creates 50 carefully designed IoT devices across Indian smart city/hospital locations.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db
from models import Device, RiskAssessment, MigrationPlan, Alert
from ml.classifier import QuantumGuardClassifier
from policy_engine import MigrationPolicyEngine
from config import FEATURE_COLUMNS

# Initialise classifier and policy engine
classifier = QuantumGuardClassifier()
policy_engine = MigrationPolicyEngine()


# ---------------------------------------------------------------------------
# 50 curated demo devices
# ---------------------------------------------------------------------------

DEMO_DEVICES = [
    # === 10 CRITICAL devices ===
    {"device_id": "CRIT-MED-001", "device_type": "medical_wearable", "encryption_algorithm": "RSA-1024",
     "data_sensitivity": 4, "data_retention_years": 15, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 1, "cpu_mhz": 160, "ram_kb": 256, "key_rotation_days": 365,
     "deployment_age_years": 6, "num_connected_devices": 12, "data_volume_mb_per_day": 5.2,
     "location": "Mumbai Hospital Network"},

    {"device_id": "CRIT-MED-002", "device_type": "medical_wearable", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 4, "data_retention_years": 20, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 180,
     "deployment_age_years": 4, "num_connected_devices": 8, "data_volume_mb_per_day": 12.0,
     "location": "Chennai Medical College"},

    {"device_id": "CRIT-IND-001", "device_type": "industrial_controller", "encryption_algorithm": "3DES",
     "data_sensitivity": 3, "data_retention_years": 12, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 1000, "ram_kb": 4096, "key_rotation_days": 365,
     "deployment_age_years": 10, "num_connected_devices": 45, "data_volume_mb_per_day": 150.0,
     "location": "Delhi Industrial Zone SCADA"},

    {"device_id": "CRIT-IND-002", "device_type": "industrial_controller", "encryption_algorithm": "RSA-1024",
     "data_sensitivity": 4, "data_retention_years": 18, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 1200, "ram_kb": 8192, "key_rotation_days": 90,
     "deployment_age_years": 12, "num_connected_devices": 120, "data_volume_mb_per_day": 500.0,
     "location": "Jamshedpur Steel Plant"},

    {"device_id": "CRIT-AV-001", "device_type": "autonomous_vehicle_sensor", "encryption_algorithm": "ECC-256",
     "data_sensitivity": 4, "data_retention_years": 10, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 3000, "ram_kb": 16384, "key_rotation_days": 30,
     "deployment_age_years": 2, "num_connected_devices": 50, "data_volume_mb_per_day": 800.0,
     "location": "Bangalore Autonomous Transit"},

    {"device_id": "CRIT-AV-002", "device_type": "autonomous_vehicle_sensor", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 4, "data_retention_years": 12, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 2000, "ram_kb": 8192, "key_rotation_days": 60,
     "deployment_age_years": 3, "num_connected_devices": 35, "data_volume_mb_per_day": 600.0,
     "location": "Pune Smart Highway"},

    {"device_id": "CRIT-MED-003", "device_type": "medical_wearable", "encryption_algorithm": "3DES",
     "data_sensitivity": 3, "data_retention_years": 10, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 1, "cpu_mhz": 80, "ram_kb": 128, "key_rotation_days": 365,
     "deployment_age_years": 8, "num_connected_devices": 5, "data_volume_mb_per_day": 2.1,
     "location": "Hyderabad ICU Ward"},

    {"device_id": "CRIT-SEC-001", "device_type": "security_camera", "encryption_algorithm": "RSA-1024",
     "data_sensitivity": 3, "data_retention_years": 7, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 1500, "ram_kb": 4096, "key_rotation_days": 365,
     "deployment_age_years": 6, "num_connected_devices": 80, "data_volume_mb_per_day": 950.0,
     "location": "Delhi Metro Surveillance"},

    {"device_id": "CRIT-WAT-001", "device_type": "water_treatment_sensor", "encryption_algorithm": "3DES",
     "data_sensitivity": 4, "data_retention_years": 15, "network_exposure": 0, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 365,
     "deployment_age_years": 11, "num_connected_devices": 25, "data_volume_mb_per_day": 35.0,
     "location": "Chennai Desalination Plant"},

    {"device_id": "CRIT-ENG-001", "device_type": "energy_meter", "encryption_algorithm": "RSA-1024",
     "data_sensitivity": 3, "data_retention_years": 14, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 256, "key_rotation_days": 365,
     "deployment_age_years": 9, "num_connected_devices": 200, "data_volume_mb_per_day": 85.0,
     "location": "Mumbai Power Distribution"},

    # === 15 HIGH devices ===
    {"device_id": "HIGH-MED-001", "device_type": "medical_wearable", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 2, "data_retention_years": 8, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 90,
     "deployment_age_years": 3, "num_connected_devices": 15, "data_volume_mb_per_day": 8.5,
     "location": "Kolkata Hospital Network"},

    {"device_id": "HIGH-ENG-001", "device_type": "energy_meter", "encryption_algorithm": "ECC-256",
     "data_sensitivity": 2, "data_retention_years": 10, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1000, "ram_kb": 2048, "key_rotation_days": 60,
     "deployment_age_years": 5, "num_connected_devices": 350, "data_volume_mb_per_day": 120.0,
     "location": "Delhi Power Grid"},

    {"device_id": "HIGH-ENG-002", "device_type": "energy_meter", "encryption_algorithm": "ECC-384",
     "data_sensitivity": 3, "data_retention_years": 8, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 1200, "ram_kb": 4096, "key_rotation_days": 90,
     "deployment_age_years": 4, "num_connected_devices": 180, "data_volume_mb_per_day": 95.0,
     "location": "Bangalore Smart Grid"},

    {"device_id": "HIGH-SEC-001", "device_type": "security_camera", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 2, "data_retention_years": 7, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 1500, "ram_kb": 4096, "key_rotation_days": 180,
     "deployment_age_years": 5, "num_connected_devices": 60, "data_volume_mb_per_day": 750.0,
     "location": "Chennai Airport Security"},

    {"device_id": "HIGH-SEC-002", "device_type": "security_camera", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 3, "data_retention_years": 6, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 2000, "ram_kb": 8192, "key_rotation_days": 120,
     "deployment_age_years": 4, "num_connected_devices": 45, "data_volume_mb_per_day": 680.0,
     "location": "Mumbai Financial District"},

    {"device_id": "HIGH-IND-001", "device_type": "industrial_controller", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 2, "data_retention_years": 9, "network_exposure": 0, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 1500, "ram_kb": 8192, "key_rotation_days": 60,
     "deployment_age_years": 7, "num_connected_devices": 90, "data_volume_mb_per_day": 300.0,
     "location": "Bangalore Factory Floor"},

    {"device_id": "HIGH-IND-002", "device_type": "industrial_controller", "encryption_algorithm": "AES-128",
     "data_sensitivity": 3, "data_retention_years": 6, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1200, "ram_kb": 4096, "key_rotation_days": 30,
     "deployment_age_years": 4, "num_connected_devices": 65, "data_volume_mb_per_day": 220.0,
     "location": "Pune Manufacturing Hub"},

    {"device_id": "HIGH-WAT-001", "device_type": "water_treatment_sensor", "encryption_algorithm": "ECC-256",
     "data_sensitivity": 2, "data_retention_years": 8, "network_exposure": 0, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 90,
     "deployment_age_years": 6, "num_connected_devices": 30, "data_volume_mb_per_day": 45.0,
     "location": "Jaipur Water Works"},

    {"device_id": "HIGH-SH-001", "device_type": "smart_home", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 2, "data_retention_years": 6, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 180,
     "deployment_age_years": 5, "num_connected_devices": 20, "data_volume_mb_per_day": 15.0,
     "location": "Noida Smart Apartments"},

    {"device_id": "HIGH-AV-001", "device_type": "autonomous_vehicle_sensor", "encryption_algorithm": "ECC-384",
     "data_sensitivity": 2, "data_retention_years": 7, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 3000, "ram_kb": 16384, "key_rotation_days": 30,
     "deployment_age_years": 1, "num_connected_devices": 40, "data_volume_mb_per_day": 700.0,
     "location": "Hyderabad Test Track"},

    {"device_id": "HIGH-MED-002", "device_type": "medical_wearable", "encryption_algorithm": "AES-128",
     "data_sensitivity": 3, "data_retention_years": 5, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 160, "ram_kb": 256, "key_rotation_days": 90,
     "deployment_age_years": 2, "num_connected_devices": 10, "data_volume_mb_per_day": 4.0,
     "location": "Lucknow Health Center"},

    {"device_id": "HIGH-ENG-003", "device_type": "energy_meter", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 2, "data_retention_years": 7, "network_exposure": 1, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 365,
     "deployment_age_years": 6, "num_connected_devices": 150, "data_volume_mb_per_day": 75.0,
     "location": "Ahmedabad Substation"},

    {"device_id": "HIGH-SEC-003", "device_type": "security_camera", "encryption_algorithm": "ECC-256",
     "data_sensitivity": 3, "data_retention_years": 6, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1500, "ram_kb": 4096, "key_rotation_days": 60,
     "deployment_age_years": 3, "num_connected_devices": 55, "data_volume_mb_per_day": 820.0,
     "location": "Goa Tourism Security"},

    {"device_id": "HIGH-WAT-002", "device_type": "water_treatment_sensor", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 2, "data_retention_years": 10, "network_exposure": 0, "update_capable": 0,
     "battery_powered": 0, "cpu_mhz": 1000, "ram_kb": 2048, "key_rotation_days": 120,
     "deployment_age_years": 7, "num_connected_devices": 40, "data_volume_mb_per_day": 60.0,
     "location": "Vishakhapatnam Treatment Plant"},

    {"device_id": "HIGH-IND-003", "device_type": "industrial_controller", "encryption_algorithm": "ECC-256",
     "data_sensitivity": 3, "data_retention_years": 8, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 2000, "ram_kb": 8192, "key_rotation_days": 45,
     "deployment_age_years": 3, "num_connected_devices": 75, "data_volume_mb_per_day": 350.0,
     "location": "Coimbatore Textile Mill"},

    # === 15 MEDIUM devices ===
    {"device_id": "MED-SH-001", "device_type": "smart_home", "encryption_algorithm": "AES-128",
     "data_sensitivity": 1, "data_retention_years": 2, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 30,
     "deployment_age_years": 2, "num_connected_devices": 15, "data_volume_mb_per_day": 8.0,
     "location": "Chennai Smart City"},

    {"device_id": "MED-SH-002", "device_type": "smart_home", "encryption_algorithm": "ECC-256",
     "data_sensitivity": 1, "data_retention_years": 3, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 160, "ram_kb": 256, "key_rotation_days": 60,
     "deployment_age_years": 3, "num_connected_devices": 10, "data_volume_mb_per_day": 5.0,
     "location": "Bangalore Tech Park"},

    {"device_id": "MED-ENV-001", "device_type": "environmental_sensor", "encryption_algorithm": "AES-128",
     "data_sensitivity": 2, "data_retention_years": 3, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 80, "ram_kb": 64, "key_rotation_days": 90,
     "deployment_age_years": 4, "num_connected_devices": 5, "data_volume_mb_per_day": 1.2,
     "location": "Western Ghats Research Station"},

    {"device_id": "MED-ENV-002", "device_type": "environmental_sensor", "encryption_algorithm": "ChaCha20",
     "data_sensitivity": 2, "data_retention_years": 4, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 80, "ram_kb": 128, "key_rotation_days": 120,
     "deployment_age_years": 3, "num_connected_devices": 8, "data_volume_mb_per_day": 2.5,
     "location": "Sundarbans Delta Monitoring"},

    {"device_id": "MED-SH-003", "device_type": "smart_home", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 1, "data_retention_years": 2, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 60,
     "deployment_age_years": 2, "num_connected_devices": 25, "data_volume_mb_per_day": 12.0,
     "location": "Gurgaon Smart Home Complex"},

    {"device_id": "MED-ENG-001", "device_type": "energy_meter", "encryption_algorithm": "ECC-256",
     "data_sensitivity": 1, "data_retention_years": 3, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1000, "ram_kb": 2048, "key_rotation_days": 90,
     "deployment_age_years": 2, "num_connected_devices": 100, "data_volume_mb_per_day": 50.0,
     "location": "Mysore Solar Farm"},

    {"device_id": "MED-SEC-001", "device_type": "security_camera", "encryption_algorithm": "ChaCha20",
     "data_sensitivity": 2, "data_retention_years": 3, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1500, "ram_kb": 4096, "key_rotation_days": 30,
     "deployment_age_years": 1, "num_connected_devices": 30, "data_volume_mb_per_day": 500.0,
     "location": "Kochi Port Authority"},

    {"device_id": "MED-IND-001", "device_type": "industrial_controller", "encryption_algorithm": "AES-128",
     "data_sensitivity": 2, "data_retention_years": 5, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1500, "ram_kb": 8192, "key_rotation_days": 45,
     "deployment_age_years": 9, "num_connected_devices": 55, "data_volume_mb_per_day": 180.0,
     "location": "Vizag Shipyard"},

    {"device_id": "MED-WAT-001", "device_type": "water_treatment_sensor", "encryption_algorithm": "AES-128",
     "data_sensitivity": 1, "data_retention_years": 3, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 60,
     "deployment_age_years": 3, "num_connected_devices": 15, "data_volume_mb_per_day": 20.0,
     "location": "Udaipur Lake Monitoring"},

    {"device_id": "MED-SH-004", "device_type": "smart_home", "encryption_algorithm": "ChaCha20",
     "data_sensitivity": 2, "data_retention_years": 2, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 160, "ram_kb": 256, "key_rotation_days": 30,
     "deployment_age_years": 1, "num_connected_devices": 12, "data_volume_mb_per_day": 6.0,
     "location": "Chandigarh Smart Residences"},

    {"device_id": "MED-ENV-003", "device_type": "environmental_sensor", "encryption_algorithm": "RSA-2048",
     "data_sensitivity": 0, "data_retention_years": 2, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 80, "ram_kb": 64, "key_rotation_days": 180,
     "deployment_age_years": 5, "num_connected_devices": 3, "data_volume_mb_per_day": 0.5,
     "location": "Ladakh Weather Station"},

    {"device_id": "MED-ENG-002", "device_type": "energy_meter", "encryption_algorithm": "AES-128",
     "data_sensitivity": 2, "data_retention_years": 4, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1000, "ram_kb": 2048, "key_rotation_days": 60,
     "deployment_age_years": 10, "num_connected_devices": 80, "data_volume_mb_per_day": 40.0,
     "location": "Trivandrum Grid Station"},

    {"device_id": "MED-AV-001", "device_type": "autonomous_vehicle_sensor", "encryption_algorithm": "AES-256",
     "data_sensitivity": 2, "data_retention_years": 5, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 3000, "ram_kb": 16384, "key_rotation_days": 14,
     "deployment_age_years": 9, "num_connected_devices": 30, "data_volume_mb_per_day": 450.0,
     "location": "Chennai Test Circuit"},

    {"device_id": "MED-SEC-002", "device_type": "security_camera", "encryption_algorithm": "AES-128",
     "data_sensitivity": 1, "data_retention_years": 2, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1200, "ram_kb": 2048, "key_rotation_days": 30,
     "deployment_age_years": 2, "num_connected_devices": 20, "data_volume_mb_per_day": 350.0,
     "location": "Indore Shopping Mall"},

    {"device_id": "MED-MED-001", "device_type": "medical_wearable", "encryption_algorithm": "AES-256",
     "data_sensitivity": 2, "data_retention_years": 3, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 30,
     "deployment_age_years": 9, "num_connected_devices": 6, "data_volume_mb_per_day": 3.0,
     "location": "Vellore CMC Hospital"},

    # === 10 LOW devices ===
    {"device_id": "LOW-ENV-001", "device_type": "environmental_sensor", "encryption_algorithm": "AES-256",
     "data_sensitivity": 0, "data_retention_years": 2, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 80, "ram_kb": 64, "key_rotation_days": 30,
     "deployment_age_years": 1, "num_connected_devices": 5, "data_volume_mb_per_day": 0.5,
     "location": "IIT Madras Campus"},

    {"device_id": "LOW-ENV-002", "device_type": "environmental_sensor", "encryption_algorithm": "Kyber-512",
     "data_sensitivity": 0, "data_retention_years": 1, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 160, "ram_kb": 256, "key_rotation_days": 14,
     "deployment_age_years": 0, "num_connected_devices": 10, "data_volume_mb_per_day": 1.0,
     "location": "VIT Chennai Campus"},

    {"device_id": "LOW-SH-001", "device_type": "smart_home", "encryption_algorithm": "AES-256",
     "data_sensitivity": 0, "data_retention_years": 1, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 30,
     "deployment_age_years": 1, "num_connected_devices": 8, "data_volume_mb_per_day": 3.0,
     "location": "Pondicherry Smart Village"},

    {"device_id": "LOW-SH-002", "device_type": "smart_home", "encryption_algorithm": "Kyber-768",
     "data_sensitivity": 1, "data_retention_years": 2, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1000, "ram_kb": 2048, "key_rotation_days": 30,
     "deployment_age_years": 0, "num_connected_devices": 15, "data_volume_mb_per_day": 10.0,
     "location": "Bangalore PQC Pilot"},

    {"device_id": "LOW-ENV-003", "device_type": "environmental_sensor", "encryption_algorithm": "AES-256",
     "data_sensitivity": 1, "data_retention_years": 1, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 80, "ram_kb": 128, "key_rotation_days": 60,
     "deployment_age_years": 2, "num_connected_devices": 3, "data_volume_mb_per_day": 0.8,
     "location": "Srinagar AQI Monitor"},

    {"device_id": "LOW-ENG-001", "device_type": "energy_meter", "encryption_algorithm": "AES-256",
     "data_sensitivity": 1, "data_retention_years": 3, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1000, "ram_kb": 2048, "key_rotation_days": 28,
     "deployment_age_years": 1, "num_connected_devices": 50, "data_volume_mb_per_day": 25.0,
     "location": "Jodhpur Solar Park"},

    {"device_id": "LOW-SH-003", "device_type": "smart_home", "encryption_algorithm": "HYBRID-ECC-Kyber",
     "data_sensitivity": 1, "data_retention_years": 2, "network_exposure": 1, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 1200, "ram_kb": 4096, "key_rotation_days": 14,
     "deployment_age_years": 0, "num_connected_devices": 20, "data_volume_mb_per_day": 15.0,
     "location": "Hyderabad Smart Township"},

    {"device_id": "LOW-WAT-001", "device_type": "water_treatment_sensor", "encryption_algorithm": "AES-256",
     "data_sensitivity": 1, "data_retention_years": 2, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 45,
     "deployment_age_years": 1, "num_connected_devices": 12, "data_volume_mb_per_day": 10.0,
     "location": "Nagpur Water Authority"},

    {"device_id": "LOW-IND-001", "device_type": "industrial_controller", "encryption_algorithm": "AES-256",
     "data_sensitivity": 1, "data_retention_years": 2, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 0, "cpu_mhz": 2000, "ram_kb": 8192, "key_rotation_days": 30,
     "deployment_age_years": 1, "num_connected_devices": 40, "data_volume_mb_per_day": 100.0,
     "location": "Surat Diamond Processing"},

    {"device_id": "LOW-MED-001", "device_type": "medical_wearable", "encryption_algorithm": "Kyber-512",
     "data_sensitivity": 1, "data_retention_years": 3, "network_exposure": 0, "update_capable": 1,
     "battery_powered": 1, "cpu_mhz": 240, "ram_kb": 512, "key_rotation_days": 30,
     "deployment_age_years": 0, "num_connected_devices": 4, "data_volume_mb_per_day": 2.0,
     "location": "AIIMS Delhi PQC Trial"},
]


def seed_demo_data():
    """Seed the database with 50 demo IoT devices and assess them all."""
    init_db()
    db = get_db()

    # Check if data already exists
    existing = db.query(Device).count()
    if existing >= 50:
        print(f"[Seed] Database already has {existing} devices. Skipping seed.")
        db.close()
        return

    # Clear any partial data
    if existing > 0:
        print(f"[Seed] Clearing {existing} existing devices for re-seed...")
        db.query(Alert).delete()
        db.query(MigrationPlan).delete()
        db.query(RiskAssessment).delete()
        db.query(Device).delete()
        db.commit()

    print("[Seed] Inserting 50 demo devices...")
    counters = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

    for dev_data in DEMO_DEVICES:
        # Insert device
        device = Device(
            device_id=dev_data["device_id"],
            device_type=dev_data["device_type"],
            encryption_algorithm=dev_data["encryption_algorithm"],
            data_sensitivity=dev_data["data_sensitivity"],
            data_retention_years=dev_data["data_retention_years"],
            network_exposure=dev_data["network_exposure"],
            update_capable=dev_data["update_capable"],
            battery_powered=dev_data["battery_powered"],
            cpu_mhz=dev_data["cpu_mhz"],
            ram_kb=dev_data["ram_kb"],
            key_rotation_days=dev_data["key_rotation_days"],
            deployment_age_years=dev_data["deployment_age_years"],
            num_connected_devices=dev_data["num_connected_devices"],
            data_volume_mb_per_day=dev_data["data_volume_mb_per_day"],
            location=dev_data.get("location", "Unknown"),
        )
        db.add(device)
        db.flush()

        # Classify device
        try:
            classification = classifier.classify(dev_data)
        except Exception as e:
            print(f"  [!] Classification failed for {dev_data['device_id']}: {e}")
            classification = {
                "risk_level": "MEDIUM",
                "risk_score": 0.5,
                "confidence_scores": {"LOW": 10, "MEDIUM": 60, "HIGH": 20, "CRITICAL": 10},
            }

        risk_level = classification["risk_level"]
        risk_score = classification["risk_score"]
        counters[risk_level] += 1

        # Policy evaluation
        policy = policy_engine.evaluate(dev_data, risk_level, risk_score)

        # Store risk assessment
        assessment = RiskAssessment(
            device_id=dev_data["device_id"],
            risk_level=risk_level,
            risk_score=risk_score,
            recommended_strategy=policy["strategy"],
            recommended_algorithm=policy["recommended_algorithm"],
            reasoning=policy["reasoning"],
        )
        db.add(assessment)

        # Store migration plan
        plan = MigrationPlan(
            device_id=dev_data["device_id"],
            current_algorithm=dev_data["encryption_algorithm"],
            target_algorithm=policy["recommended_algorithm"],
            migration_phase=policy["migration_phase"],
            estimated_effort=policy["estimated_effort"],
            priority_score=policy["priority_score"],
            notes=policy["notes"],
            status="Pending",
        )
        db.add(plan)

        # Create alerts for CRITICAL and HIGH risk devices
        if risk_level == "CRITICAL":
            alert = Alert(
                device_id=dev_data["device_id"],
                severity="CRITICAL",
                title=f"Critical Quantum Risk: {dev_data['device_id']}",
                message=(
                    f"{dev_data['device_type'].replace('_', ' ').title()} at "
                    f"{dev_data.get('location', 'Unknown')} uses {dev_data['encryption_algorithm']} "
                    f"with sensitivity level {dev_data['data_sensitivity']}. "
                    f"Immediate migration to post-quantum cryptography required."
                ),
            )
            db.add(alert)
        elif risk_level == "HIGH":
            alert = Alert(
                device_id=dev_data["device_id"],
                severity="HIGH",
                title=f"High Quantum Risk: {dev_data['device_id']}",
                message=(
                    f"{dev_data['device_type'].replace('_', ' ').title()} at "
                    f"{dev_data.get('location', 'Unknown')} uses {dev_data['encryption_algorithm']}. "
                    f"Plan hybrid cryptographic migration within 3–12 months."
                ),
            )
            db.add(alert)

    db.commit()
    db.close()

    print("\n" + "=" * 60)
    print(f"  Seeded 50 devices: "
          f"{counters['CRITICAL']} CRITICAL, "
          f"{counters['HIGH']} HIGH, "
          f"{counters['MEDIUM']} MEDIUM, "
          f"{counters['LOW']} LOW")
    print("=" * 60)

    return counters


if __name__ == "__main__":
    print("=" * 60)
    print("  QuantumGuard AI — Demo Data Seeder")
    print("=" * 60)
    seed_demo_data()
