"""
QuantumGuard AI — Model Training & Evaluation
Trains Random Forest, GradientBoosting, and Logistic Regression.
Picks the best model and saves it along with preprocessor and metadata.
"""
import os
import sys
import json
import time
import warnings
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import LabelEncoder, StandardScaler, OrdinalEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    f1_score,
    accuracy_score,
)
from imblearn.over_sampling import SMOTE

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import (
    DATASET_PATH, MODEL_PATH, PREPROCESSOR_PATH, MODEL_METADATA_PATH,
    CATEGORICAL_FEATURES, NUMERIC_FEATURES, ORDINAL_FEATURES,
    FEATURE_COLUMNS, RISK_LABELS,
)


def load_and_prepare_data():
    """Load dataset and prepare features/target."""
    print("[1/6] Loading dataset...")
    df = pd.read_csv(DATASET_PATH)
    print(f"  Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"  Class distribution:\n{df['risk_label'].value_counts().to_string()}\n")

    X = df[FEATURE_COLUMNS].copy()
    y = df["risk_label"].copy()

    return X, y, df


def build_preprocessor():
    """Build a ColumnTransformer pipeline for preprocessing."""
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
             CATEGORICAL_FEATURES),
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("ord", "passthrough", ORDINAL_FEATURES),
        ],
        remainder="drop",
    )
    return preprocessor


def train_and_evaluate():
    """Train models, evaluate, and save the best one."""
    X, y, df = load_and_prepare_data()

    # Encode target
    label_encoder = LabelEncoder()
    label_encoder.classes_ = np.array(RISK_LABELS)
    y_encoded = label_encoder.transform(y)

    # Build preprocessor
    print("[2/6] Building preprocessing pipeline...")
    preprocessor = build_preprocessor()
    preprocessor.fit(X)
    X_transformed = preprocessor.transform(X)

    # Apply SMOTE for class balancing
    print("[3/6] Applying SMOTE for class balancing...")
    smote = SMOTE(random_state=42)
    X_balanced, y_balanced = smote.fit_resample(X_transformed, y_encoded)
    print(f"  After SMOTE: {len(X_balanced)} samples")
    for i, label in enumerate(RISK_LABELS):
        count = np.sum(y_balanced == i)
        print(f"    {label}: {count}")

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
    )
    print(f"\n  Train: {len(X_train)}, Test: {len(X_test)}")

    # Define models
    models = {
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=None, class_weight="balanced",
            random_state=42, n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.1, random_state=42
        ),
        "Logistic Regression": LogisticRegression(
            max_iter=1000, random_state=42
        ),
    }

    # Stratified 5-fold cross-validation
    print("\n[4/6] Stratified 5-Fold Cross-Validation...")
    print("-" * 55)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_results = {}

    for name, model in models.items():
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1_macro", n_jobs=-1)
        cv_results[name] = scores
        print(f"  {name:25s} | CV F1-Macro: {scores.mean():.4f} (+/- {scores.std():.4f})")

    # Train all models on full training set
    print("\n[5/6] Training all models on full training set...")
    trained_models = {}
    test_results = {}

    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - t0
        y_pred = model.predict(X_test)

        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average="macro")

        # ROC-AUC (one-vs-rest)
        if hasattr(model, "predict_proba"):
            y_proba = model.predict_proba(X_test)
            try:
                auc = roc_auc_score(y_test, y_proba, multi_class="ovr", average="macro")
            except ValueError:
                auc = 0.0
        else:
            auc = 0.0

        trained_models[name] = model
        test_results[name] = {
            "accuracy": acc,
            "f1_macro": f1,
            "roc_auc": auc,
            "train_time": train_time,
            "y_pred": y_pred,
        }

        print(f"\n  --- {name} ---")
        print(f"  Accuracy:  {acc:.4f}")
        print(f"  Macro F1:  {f1:.4f}")
        print(f"  ROC AUC:   {auc:.4f}")
        print(f"  Train Time: {train_time:.2f}s")
        print(f"\n  Classification Report:")
        print(classification_report(
            y_test, y_pred, target_names=RISK_LABELS, digits=4
        ))

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"  Confusion Matrix:")
        header = "          " + "  ".join(f"{l:>8s}" for l in RISK_LABELS)
        print(header)
        for i, row_vals in enumerate(cm):
            row_str = f"  {RISK_LABELS[i]:>8s} " + "  ".join(f"{v:>8d}" for v in row_vals)
            print(row_str)

    # Feature importance (Random Forest)
    rf_model = trained_models["Random Forest"]
    feature_names = (
        CATEGORICAL_FEATURES + NUMERIC_FEATURES + ORDINAL_FEATURES
    )
    importances = rf_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]

    print("\n  Top 10 Feature Importances (Random Forest):")
    print("  " + "-" * 40)
    for rank, idx in enumerate(sorted_idx[:10], 1):
        fname = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
        print(f"  {rank:2d}. {fname:30s}: {importances[idx]:.4f}")

    # Pick best model
    best_name = max(test_results, key=lambda k: test_results[k]["f1_macro"])
    best_model = trained_models[best_name]
    best_info = test_results[best_name]

    print("\n" + "=" * 60)
    print(f"  Best Model: {best_name} | "
          f"Test Accuracy: {best_info['accuracy'] * 100:.1f}% | "
          f"Macro F1: {best_info['f1_macro']:.2f}")
    print("=" * 60)

    # Save
    print("\n[6/6] Saving model artifacts...")
    joblib.dump(best_model, MODEL_PATH)
    print(f"  [✓] Model saved to: {MODEL_PATH}")

    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    print(f"  [✓] Preprocessor saved to: {PREPROCESSOR_PATH}")

    # Metadata
    feature_importance_dict = {}
    if hasattr(best_model, "feature_importances_"):
        for idx in sorted_idx[:len(feature_names)]:
            fname = feature_names[idx] if idx < len(feature_names) else f"feature_{idx}"
            feature_importance_dict[fname] = round(float(importances[idx]), 4)

    metadata = {
        "model_type": best_name,
        "accuracy": round(best_info["accuracy"], 4),
        "f1_score": round(best_info["f1_macro"], 4),
        "roc_auc": round(best_info["roc_auc"], 4),
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_training_samples": int(len(X_balanced)),
        "test_samples": int(len(X_test)),
        "class_distribution": {
            label: int(np.sum(y_balanced == i)) for i, label in enumerate(RISK_LABELS)
        },
        "feature_names": feature_names,
        "feature_importances": feature_importance_dict,
        "cv_scores": {
            name: {
                "mean": round(float(scores.mean()), 4),
                "std": round(float(scores.std()), 4),
            }
            for name, scores in cv_results.items()
        },
        "all_model_results": {
            name: {
                "accuracy": round(res["accuracy"], 4),
                "f1_macro": round(res["f1_macro"], 4),
                "roc_auc": round(res["roc_auc"], 4),
            }
            for name, res in test_results.items()
        },
    }

    with open(MODEL_METADATA_PATH, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  [✓] Metadata saved to: {MODEL_METADATA_PATH}")

    print("\n[✓] Training complete!")
    return best_model, preprocessor, metadata


if __name__ == "__main__":
    print("=" * 60)
    print("  QuantumGuard AI — Model Training Pipeline")
    print("=" * 60)
    train_and_evaluate()
