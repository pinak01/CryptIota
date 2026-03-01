"""
QuantumGuard AI — ML Inference Wrapper
Loads the trained model + preprocessor and provides classification methods.
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    MODEL_PATH, PREPROCESSOR_PATH, MODEL_METADATA_PATH,
    FEATURE_COLUMNS, RISK_LABELS,
)


class QuantumGuardClassifier:
    """Inference wrapper for the trained QuantumGuard risk classifier."""

    def __init__(self):
        self.model = None
        self.preprocessor = None
        self.metadata = None
        self.loaded = False
        self._load()

    def _load(self):
        """Load the trained model, preprocessor, and metadata."""
        if not os.path.exists(MODEL_PATH):
            print(f"[WARNING] Model not found at {MODEL_PATH}. "
                  "Run train_model.py first.")
            return

        if not os.path.exists(PREPROCESSOR_PATH):
            print(f"[WARNING] Preprocessor not found at {PREPROCESSOR_PATH}. "
                  "Run train_model.py first.")
            return

        self.model = joblib.load(MODEL_PATH)
        self.preprocessor = joblib.load(PREPROCESSOR_PATH)

        if os.path.exists(MODEL_METADATA_PATH):
            with open(MODEL_METADATA_PATH, "r") as f:
                self.metadata = json.load(f)

        self.loaded = True
        print(f"[Classifier] Model loaded: {self.metadata.get('model_type', 'Unknown')} "
              f"(Accuracy: {self.metadata.get('accuracy', 'N/A')})")

    def classify(self, device_data: dict) -> dict:
        """
        Classify a single device and return risk assessment.

        Args:
            device_data: dict with keys matching FEATURE_COLUMNS

        Returns:
            dict with risk_level, risk_score, confidence_scores
        """
        if not self.loaded:
            raise RuntimeError("Model not loaded. Run train_model.py first.")

        # Build feature vector
        features = {}
        for col in FEATURE_COLUMNS:
            if col not in device_data:
                raise ValueError(f"Missing required feature: {col}")
            features[col] = device_data[col]

        df = pd.DataFrame([features])
        X = self.preprocessor.transform(df)

        # Predict class and probabilities
        prediction = self.model.predict(X)[0]
        risk_level = RISK_LABELS[prediction]

        # Get probability scores
        probabilities = self.model.predict_proba(X)[0]
        confidence_scores = {
            label: round(float(prob) * 100, 2)
            for label, prob in zip(RISK_LABELS, probabilities)
        }

        # Risk score: weighted combination based on probabilities
        risk_weights = {"LOW": 0.1, "MEDIUM": 0.4, "HIGH": 0.7, "CRITICAL": 1.0}
        risk_score = sum(
            prob * risk_weights[label]
            for label, prob in zip(RISK_LABELS, probabilities)
        )
        risk_score = round(float(risk_score), 4)

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "confidence_scores": confidence_scores,
        }

    def classify_batch(self, devices: list) -> list:
        """Classify a batch of devices.

        Args:
            devices: list of dicts, each with keys matching FEATURE_COLUMNS

        Returns:
            list of classification result dicts
        """
        if not self.loaded:
            raise RuntimeError("Model not loaded. Run train_model.py first.")

        results = []
        for device_data in devices:
            try:
                result = self.classify(device_data)
                result["device_id"] = device_data.get("device_id", "unknown")
                results.append(result)
            except Exception as e:
                results.append({
                    "device_id": device_data.get("device_id", "unknown"),
                    "error": str(e),
                })
        return results

    def get_model_info(self) -> dict:
        """Return model metadata for the API."""
        if not self.metadata:
            return {"error": "Model not loaded"}

        return {
            "model_type": self.metadata.get("model_type"),
            "accuracy": self.metadata.get("accuracy"),
            "f1_score": self.metadata.get("f1_score"),
            "roc_auc": self.metadata.get("roc_auc"),
            "feature_importances": self.metadata.get("feature_importances", {}),
            "trained_at": self.metadata.get("trained_at"),
            "total_training_samples": self.metadata.get("total_training_samples"),
            "class_distribution": self.metadata.get("class_distribution"),
            "feature_names": self.metadata.get("feature_names"),
        }
