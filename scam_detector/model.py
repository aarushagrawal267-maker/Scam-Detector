"""Loads the trained machine-learning model and gives a scam probability.

The model file is produced by ``training/train_baseline.py``. It is a
scikit-learn Pipeline: TF-IDF features -> Logistic Regression.

Security note: ``joblib.load`` can run code hidden inside a file, so only ever
load model files that YOU trained. Never load a .joblib file from a stranger.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = ROOT / "models" / "baseline.joblib"
DEFAULT_META = ROOT / "models" / "baseline_meta.json"

# Used only if no trained model metadata exists yet.
FALLBACK_THRESHOLDS = {"suspicious": 0.35, "scam": 0.70}


@lru_cache(maxsize=1)
def load_model():
    """Return the trained pipeline, or ``None`` if it hasn't been trained yet."""
    path = Path(os.environ.get("SCAM_MODEL_PATH", DEFAULT_MODEL))
    if not path.exists():
        return None
    import joblib

    return joblib.load(path)


@lru_cache(maxsize=1)
def load_meta() -> dict:
    path = Path(os.environ.get("SCAM_MODEL_META", DEFAULT_META))
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"thresholds": FALLBACK_THRESHOLDS, "model_version": "rules-only"}


def thresholds() -> dict:
    return load_meta().get("thresholds", FALLBACK_THRESHOLDS)


def scam_probability(texts: list[str]) -> list[float] | None:
    """Probability (0-1) that each text is a scam, or ``None`` with no model."""
    model = load_model()
    if model is None:
        return None
    return [float(p) for p in model.predict_proba(texts)[:, 1]]
