"""
QuantumGuard AI — SQLAlchemy ORM Models
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, Float, DateTime, ForeignKey
from database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Text, unique=True, nullable=False, index=True)
    device_type = Column(Text, nullable=False)
    encryption_algorithm = Column(Text, nullable=False)
    data_sensitivity = Column(Integer, nullable=False)
    data_retention_years = Column(Integer, nullable=False)
    network_exposure = Column(Integer, nullable=False)
    update_capable = Column(Integer, nullable=False)
    battery_powered = Column(Integer, nullable=False)
    cpu_mhz = Column(Integer, nullable=False)
    ram_kb = Column(Integer, nullable=False)
    key_rotation_days = Column(Integer, nullable=False)
    deployment_age_years = Column(Integer, nullable=False)
    num_connected_devices = Column(Integer, nullable=False)
    data_volume_mb_per_day = Column(Float, nullable=False)
    location = Column(Text, default="Unknown")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "device_type": self.device_type,
            "encryption_algorithm": self.encryption_algorithm,
            "data_sensitivity": self.data_sensitivity,
            "data_retention_years": self.data_retention_years,
            "network_exposure": self.network_exposure,
            "update_capable": self.update_capable,
            "battery_powered": self.battery_powered,
            "cpu_mhz": self.cpu_mhz,
            "ram_kb": self.ram_kb,
            "key_rotation_days": self.key_rotation_days,
            "deployment_age_years": self.deployment_age_years,
            "num_connected_devices": self.num_connected_devices,
            "data_volume_mb_per_day": self.data_volume_mb_per_day,
            "location": self.location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Text, ForeignKey("devices.device_id"), nullable=False, index=True)
    risk_level = Column(Text, nullable=False)
    risk_score = Column(Float, nullable=False)
    recommended_strategy = Column(Text, nullable=False)
    recommended_algorithm = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    assessed_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "recommended_strategy": self.recommended_strategy,
            "recommended_algorithm": self.recommended_algorithm,
            "reasoning": self.reasoning,
            "assessed_at": self.assessed_at.isoformat() if self.assessed_at else None,
        }


class CryptoBenchmarkResult(Base):
    __tablename__ = "crypto_benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    algorithm = Column(Text, nullable=False)
    variant = Column(Text)
    avg_keygen_ms = Column(Float)
    avg_encrypt_ms = Column(Float)
    avg_decrypt_ms = Column(Float)
    key_size_bytes = Column(Integer)
    ciphertext_overhead_bytes = Column(Integer)
    quantum_safe = Column(Integer, default=0)
    using_liboqs = Column(Integer, default=0)
    iterations = Column(Integer)
    benchmarked_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "algorithm": self.algorithm,
            "variant": self.variant,
            "avg_keygen_ms": self.avg_keygen_ms,
            "avg_encrypt_ms": self.avg_encrypt_ms,
            "avg_decrypt_ms": self.avg_decrypt_ms,
            "key_size_bytes": self.key_size_bytes,
            "ciphertext_overhead_bytes": self.ciphertext_overhead_bytes,
            "quantum_safe": bool(self.quantum_safe),
            "using_liboqs": bool(self.using_liboqs),
            "iterations": self.iterations,
            "benchmarked_at": self.benchmarked_at.isoformat() if self.benchmarked_at else None,
        }


class MigrationPlan(Base):
    __tablename__ = "migration_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Text, ForeignKey("devices.device_id"), nullable=False, index=True)
    current_algorithm = Column(Text, nullable=False)
    target_algorithm = Column(Text, nullable=False)
    migration_phase = Column(Text, nullable=False)
    estimated_effort = Column(Text, nullable=False)
    priority_score = Column(Float, nullable=False)
    notes = Column(Text)
    status = Column(Text, default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "current_algorithm": self.current_algorithm,
            "target_algorithm": self.target_algorithm,
            "migration_phase": self.migration_phase,
            "estimated_effort": self.estimated_effort,
            "priority_score": self.priority_score,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Text, ForeignKey("devices.device_id"), nullable=False, index=True)
    severity = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    acknowledged = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "acknowledged": bool(self.acknowledged),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
