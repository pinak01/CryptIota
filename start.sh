#!/usr/bin/env bash
set -e

echo "============================================================"
echo "  QuantumGuard AI — Full-Stack Startup"
echo "============================================================"

cd "$(dirname "$0")"
ROOT_DIR="$(pwd)"

# ─── Python Backend ───────────────────────────────────────────────
echo ""
echo "[1/6] Setting up Python environment..."

cd "$ROOT_DIR/backend"

if [ ! -d "venv" ]; then
    python -m venv venv
    echo "  ✔ Virtual environment created"
fi

# Activate
source venv/Scripts/activate 2>/dev/null || source venv/bin/activate

echo "[2/6] Installing Python dependencies..."
pip install -q -r requirements.txt

echo "[3/6] Generating dataset & training ML model..."
if [ ! -f "ml/iot_dataset.csv" ]; then
    python -m ml.generate_dataset
    echo "  ✔ Dataset generated"
else
    echo "  ✔ Dataset already exists"
fi

if [ ! -f "models/quantumguard_model.pkl" ]; then
    python -m ml.train_model
    echo "  ✔ Model trained"
else
    echo "  ✔ Model already trained"
fi

echo "[4/6] Seeding demo data..."
python -c "
from database import init_db
init_db()
from seed_demo_data import seed_demo_data
seed_demo_data()
"
echo "  ✔ Demo data ready"

echo "[5/6] Starting Flask backend on http://localhost:6000 ..."
python app.py &
BACKEND_PID=$!
sleep 2

# ─── Node.js Frontend ────────────────────────────────────────────
cd "$ROOT_DIR/frontend"

echo "[6/6] Setting up frontend..."
if [ ! -d "node_modules" ]; then
    npm install
fi

echo ""
echo "============================================================"
echo "  QuantumGuard AI is running!"
echo "  ┌─────────────────────────────────────────────────┐"
echo "  │  Frontend  →  http://localhost:5173             │"
echo "  │  Backend   →  http://localhost:6000/api/health  │"
echo "  └─────────────────────────────────────────────────┘"
echo "  Press Ctrl+C to stop all services."
echo "============================================================"
echo ""

npm run dev

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null
