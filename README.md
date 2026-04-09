<div align="center">

# QuantumGuard AI

**Risk-Aware Post-Quantum Cryptographic Migration Dashboard for IoT Systems**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-REST%20API-green?logo=flask)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)
![ML](https://img.shields.io/badge/ML-XGBoost%20%7C%20RF-orange?logo=scikit-learn)

</div>

---

## Overview

QuantumGuard AI is a full-stack application that uses machine learning to assess the quantum-vulnerability risk of IoT device fleets and generates prioritized migration roadmaps to post-quantum cryptographic algorithms.

### Key Features

| Feature | Description |
|---|---|
| **ML Risk Classification** | XGBoost / Random Forest trained on 12,000 synthetic IoT profiles, 4-class (LOW → CRITICAL) |
| **Crypto Benchmarks** | Real RSA, ECDH, AES-GCM benchmarks + simulated Kyber, Dilithium, Falcon PQC algorithms |
| **Hybrid Crypto Demo** | ECDH + Kyber-512 key exchange via HKDF → AES-256-GCM session key |
| **Policy Engine** | Automated migration strategy generation with weighted priority scoring |
| **Interactive Dashboard** | React frontend with Recharts: pie/bar charts, heatmap, kanban migration board |
| **CSV Bulk Upload** | Upload device CSVs for instant batch classification |

---

## Architecture

```
quantumguard-ai/
├── backend/
│   ├── app.py                    # Flask REST API (17+ endpoints)
│   ├── config.py                 # All configuration constants
│   ├── database.py               # SQLAlchemy + SQLite setup
│   ├── models.py                 # 5 ORM models (Device, RiskAssessment, etc.)
│   ├── policy_engine.py          # Risk → migration strategy mapper
│   ├── report_generator.py       # Per-device migration reports
│   ├── seed_demo_data.py         # 50 curated demo IoT devices
│   ├── requirements.txt
│   ├── crypto/
│   │   ├── classical_crypto.py   # RSA, ECDH, AES-GCM (cryptography lib)
│   │   ├── pqc_crypto.py         # Kyber, Dilithium, Falcon (liboqs / sim)
│   │   ├── hybrid_crypto.py      # ECDH + Kyber → HKDF → AES-256-GCM
│   │   └── benchmark.py          # Orchestrator for all benchmarks
│   └── ml/
│       ├── generate_dataset.py   # Synthetic 12K-row IoT dataset
│       ├── train_model.py        # Train RF, GBC, LR; save best model
│       └── classifier.py         # Inference wrapper with confidence scores
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Router (7 routes)
│   │   ├── api/apiClient.js      # Axios wrapper for all backend endpoints
│   │   ├── components/           # Navbar, RiskBadge, StatCard, etc.
│   │   └── pages/                # Dashboard, DeviceDetail, Heatmap, etc.
│   ├── index.html
│   └── vite.config.js
└── start.sh                      # One-command full-stack startup
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### One-Command Start

```bash
chmod +x start.sh
./start.sh
```

This will:
1. Create a Python virtual environment and install dependencies
2. Generate the synthetic dataset (12,000 devices)
3. Train the ML model (best of RF / GBC / LR)
4. Seed 50 demo IoT devices into SQLite
5. Start Flask backend on `http://localhost:6000`
6. Start Vite dev server on `http://localhost:5173`

### Manual Start

```bash
# Backend
cd backend
python -m venv venv && source venv/Scripts/activate
pip install -r requirements.txt
python -m ml.generate_dataset
python -m ml.train_model
python app.py

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health check |
| GET | `/api/dashboard/summary` | Full dashboard data |
| POST | `/api/classify` | Classify a single device |
| GET | `/api/devices` | List devices (filterable) |
| GET | `/api/devices/:id` | Device detail with assessments |
| POST | `/api/devices` | Add + auto-classify a device |
| POST | `/api/upload/csv` | Bulk CSV upload + classification |
| GET | `/api/benchmark` | Run crypto benchmarks |
| GET | `/api/benchmark/history` | Past benchmark runs |
| GET | `/api/migration/roadmap` | Full migration roadmap |
| GET | `/api/migration/plan/:id` | Per-device migration plan |
| GET | `/api/alerts` | List alerts (filterable) |
| POST | `/api/alerts/:id/acknowledge` | Acknowledge an alert |
| GET | `/api/report/:id` | Full device migration report |
| GET | `/api/crypto/demo/:algo` | Live crypto algorithm demo |
| GET | `/api/model/info` | ML model metadata |

---

## ML Pipeline

- **Dataset**: 12,000 synthetic IoT device profiles with deterministic risk labeling
- **Features**: 14 features including device type, encryption algorithm, sensitivity, hardware specs
- **Models**: Random Forest, Gradient Boosting, Logistic Regression
- **Balancing**: SMOTE oversampling for minority classes
- **Evaluation**: Stratified 5-fold CV + 80/20 test split, macro F1-score selection
- **Output**: 4-class risk prediction (LOW, MEDIUM, HIGH, CRITICAL) with per-class confidence

---

## Tech Stack

**Backend**: Python, Flask, SQLAlchemy, SQLite, scikit-learn, XGBoost, cryptography  
**Frontend**: React 18, Vite, Tailwind CSS v4, Recharts, Lucide Icons, Axios  
**ML**: Random Forest / Gradient Boosting, SMOTE, ColumnTransformer pipelines  
**Crypto**: Real RSA/ECDH/AES via `cryptography`, simulated Kyber/Dilithium/Falcon

---

<div align="center">
Built with ❤️ for post-quantum security research
</div>
