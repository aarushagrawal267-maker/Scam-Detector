"""Loads the trained machine-learning model and gives a scam probability.

The model file is produced by ``training/train_baseline.py``. It is a
scikit-learn Pipeline: TF-IDF features -> Logistic Regression.

Security note: ``joblib.load`` can run code hidden inside a file, so only ever
load model files that YOU trained. Never load a .joblib file from a stranger.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path

log = logging.getLogger("scam_detector.model")

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = ROOT / "models" / "baseline.joblib"
DEFAULT_META = ROOT / "models" / "baseline_meta.json"

# Used only if no trained model metadata exists yet.
FALLBACK_THRESHOLDS = {"suspicious": 0.35, "scam": 0.70}


@lru_cache(maxsize=1)
def load_model():
    """Return the trained pipeline, or ``None`` if there is no usable model.

    Without a model the checker still works with the red-flag rules only, so a
    missing or broken file is logged loudly (and shown by /api/health) instead
    of crashing every request.
    """
    path = Path(os.environ.get("SCAM_MODEL_PATH", DEFAULT_MODEL))
    if not path.exists():
        log.warning(
            "No trained model at %s, so only the red-flag rules are used. Train one with: "
            "python -m training.prepare_data && python -m training.train_baseline",
            path,
        )
        return None
    import joblib
    import sklearn

    try:
        model = joblib.load(path)
    except Exception as e:  # corrupt file, Git LFS pointer, incompatible library versions...
        log.error(
            "Could not load the model at %s (%s: %s), so only the red-flag rules are used. "
            "Install the exact versions in requirements.txt or re-train the model.",
            path, type(e).__name__, e,
        )
        return None
    if not hasattr(model, "predict_proba"):
        log.error("%s is not a probability model (%s), so only the red-flag rules are used.", path, type(model).__name__)
        return None
    trained_with = load_meta().get("sklearn_version")
    if trained_with and trained_with != sklearn.__version__:
        log.warning(
            "The model was trained with scikit-learn %s but %s is installed; scores may differ. "
            "Install the version pinned in requirements.txt.",
            trained_with, sklearn.__version__,
        )
    return model


def model_status() -> dict:
    """What /api/health and the start-up log report about the model."""
    model = load_model()
    meta = load_meta()
    return {
        "model_loaded": model is not None,
        "model_version": meta.get("model_version", "unknown") if model is not None else "rules-only",
    }


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
