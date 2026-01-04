"""Training utilities and prediction wrapper for diet recommendation model.

This module provides:
- train_from_csv(csv_path): trains a classifier and saves the pipeline to disk
- load_model(): loads the persisted pipeline
- predict_from_profile(profile): predict a diet recommendation & confidences
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Optional
import logging
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
from core.exceptions import ModelNotTrainedError

logger = logging.getLogger("services.diet_trainer")

MODELS_DIR = Path(__file__).resolve().parents[1] / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODELS_DIR / "diet_model.joblib"


def _preprocess_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize and select features from the raw CSV DataFrame.
    
    Args:
        df: Raw pandas DataFrame from CSV.
        
    Returns:
        Preprocessed DataFrame with selected feature columns.
    """
    # Standardize column names for ease of use
    df = df.rename(columns=lambda s: s.strip())

    # Select a subset of columns we will use as features
    candidates = [
        "Age",
        "Gender",
        "Weight_kg",
        "Height_cm",
        "Physical_Activity_Level",
        "Daily_Caloric_Intake",
        "Dietary_Restrictions",
        "Allergies",
        "Preferred_Cuisine",
        "Weekly_Exercise_Hours",
    ]

    available = [c for c in candidates if c in df.columns]
    X = df[available].copy()

    # Normalize categorical missing values
    for c in X.select_dtypes(include=[object]).columns:
        X[c] = X[c].fillna("Unknown").astype(str)

    # Numeric conversions
    for c in ["Age", "Weight_kg", "Height_cm", "Daily_Caloric_Intake", "Weekly_Exercise_Hours"]:
        if c in X.columns:
            X[c] = pd.to_numeric(X[c], errors="coerce")

    return X


def train_from_csv(csv_path: str, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
    """Train a RandomForest classifier on the provided CSV file.

    The pipeline uses a ColumnTransformer to impute numeric features and
    one-hot-encode categorical features. The entire sklearn pipeline is
    persisted to `data/models/diet_model.joblib`.

    Args:
        csv_path: Path to training CSV file.
        test_size: Fraction of data to use for testing (default 0.2).
        random_state: Random seed for reproducibility (default 42).
        
    Returns:
        Dictionary containing model_path, accuracy, and class labels.
        
    Raises:
        ValueError: If CSV missing 'Diet_Recommendation' column.
    """
    logger.info("Loading CSV for training: %s", csv_path)
    df = pd.read_csv(csv_path, encoding="utf-8", engine="python")

    if "Diet_Recommendation" not in df.columns:
        raise ValueError("CSV must contain 'Diet_Recommendation' column")

    X = _preprocess_frame(df)
    y = df["Diet_Recommendation"].astype(str).fillna("Unknown")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)

    # Identify numeric and categorical columns
    numeric_cols = X_train.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = X_train.select_dtypes(exclude=[np.number]).columns.tolist()

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("num", numeric_transformer, numeric_cols),
        ("cat", categorical_transformer, cat_cols)
    ])

    clf = Pipeline(steps=[
        ("pre", preprocessor),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=random_state))
    ])

    clf.fit(X_train, y_train)

    # Persist the pipeline
    joblib.dump(clf, MODEL_PATH)
    logger.info("Saved trained model to %s", MODEL_PATH)

    # Evaluate
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds, output_dict=True)

    return {
        "model_path": str(MODEL_PATH),
        "accuracy": float(acc),
        "classes": list(clf.named_steps["clf"].classes_),
        "report": report,
    }


def load_model() -> Optional[Pipeline]:
    """Load persisted model pipeline from disk.
    
    Returns:
        Trained sklearn Pipeline if model file exists, None otherwise.
    """
    if MODEL_PATH.exists():
        logger.info("Loading model from %s", MODEL_PATH)
        return joblib.load(MODEL_PATH)
    return None


def predict_from_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Predict diet recommendation from a single profile dictionary.

    The profile should contain the same feature keys as used in training.
    Missing keys are automatically filled with None before transformation.
    
    Args:
        profile: Dictionary containing user profile attributes.
        
    Returns:
        Dictionary with 'diet_recommendation', 'confidence', and 'probabilities'.
        
    Raises:
        ModelNotTrainedError: If model hasn't been trained yet.
    """
    model = load_model()
    if model is None:
        raise ModelNotTrainedError()

    # Ensure profile contains all expected candidate columns (fill missing keys with None)
    candidates = [
        "Age",
        "Gender",
        "Weight_kg",
        "Height_cm",
        "Physical_Activity_Level",
        "Daily_Caloric_Intake",
        "Dietary_Restrictions",
        "Allergies",
        "Preferred_Cuisine",
        "Weekly_Exercise_Hours",
    ]
    full_profile = {c: profile.get(c) if isinstance(profile, dict) else None for c in candidates}
    df = pd.DataFrame([full_profile])
    X = _preprocess_frame(df)

    probs = model.predict_proba(X)[0]
    classes = model.named_steps["clf"].classes_
    idx = int(np.argmax(probs))
    return {
        "diet_recommendation": str(classes[idx]),
        "confidence": float(probs[idx]),
        "probabilities": {str(c): float(p) for c, p in zip(classes, probs)}
    }