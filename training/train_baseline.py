"""Step 2: train the baseline model (TF-IDF + Logistic Regression).

Run:  python -m training.train_baseline

Why this model first?
  * It trains in seconds on a laptop, no GPU.
  * It's explainable: every word / letter-chunk gets a weight you can print.
  * It's a fair "simple" baseline the fancier models must beat.

Features
  * word TF-IDF (1-2 word phrases): catches "click here", "kyc update"
  * character TF-IDF (2-5 letter chunks inside words): catches spelling
    variations, Hinglish ("jayega" / "jaega"), typos and leetspeak ("acc0unt").
    This is what makes a simple model work across English, Hinglish and Hindi.

Choosing settings
  * C (how strongly the model is regularised) is picked on the VALIDATION set,
    never the test set.
  * class_weight="balanced": there are fewer scams than safe messages, so each
    scam counts more during training. Otherwise the model gets lazy and
    under-predicts scams.

Choosing thresholds (the most important decision!)
  Final risk = max(model probability, rule score). On the validation set:
  * SUSPICIOUS threshold = highest value that still flags >= 97% of scams.
    Missing a scam is worse than a false alarm, so we aim for high recall.
  * SCAM threshold = lowest value where >= 97% of messages above it really are
    scams (precision), so a red SCAM verdict is rarely wrong.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import FeatureUnion, Pipeline

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
MODELS = ROOT / "models"
TARGET_RECALL = 0.97
TARGET_PRECISION = 0.97


def build_pipeline(C: float = 3.0) -> Pipeline:
    features = FeatureUnion(
        [
            (
                "words",
                TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, sublinear_tf=True,
                                token_pattern=r"(?u)\b\w+\b", max_features=50000),
            ),
            (
                "chars",
                TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True,
                                max_features=150000),
            ),
        ]
    )
    clf = LogisticRegression(C=C, class_weight="balanced", max_iter=3000)
    return Pipeline([("features", features), ("clf", clf)])


def pick_thresholds(y: np.ndarray, risk: np.ndarray) -> dict:
    """Pick the SUSPICIOUS and SCAM thresholds from validation scores."""
    candidates = np.unique(np.round(risk, 4))
    suspicious = 0.0
    for t in sorted(candidates):
        if (risk[y == 1] >= t).mean() >= TARGET_RECALL:
            suspicious = float(t)  # keep raising while recall stays high enough
    scam = 1.0
    for t in sorted(candidates):
        flagged = risk >= t
        if flagged.sum() == 0:
            continue
        if y[flagged].mean() >= TARGET_PRECISION:
            scam = float(t)
            break
    scam = max(scam, suspicious)
    return {"suspicious": round(suspicious, 4), "scam": round(scam, 4)}


def main() -> None:
    train = pd.read_csv(DATA / "train.csv")
    val = pd.read_csv(DATA / "val.csv")

    best_c, best_ap = None, -1.0
    for C in (0.3, 1.0, 3.0, 10.0, 30.0):
        model = build_pipeline(C).fit(train.text, train.label)
        ap = average_precision_score(val.label, model.predict_proba(val.text)[:, 1])
        print(f"C={C:<5} validation average precision = {ap:.4f}")
        if ap > best_ap:
            best_c, best_ap = C, ap
    print(f"best C = {best_c}")

    model = build_pipeline(best_c).fit(train.text, train.label)
    MODELS.mkdir(exist_ok=True)
    joblib.dump(model, MODELS / "baseline.joblib", compress=3)

    # Thresholds for the deployed HYBRID system (model + rules), tuned on validation.
    from scam_detector import model as model_module
    from scam_detector.detector import score_texts

    model_module.load_model.cache_clear()
    scores = score_texts(val.text.tolist())
    risk = np.array([s["risk"] for s in scores])
    th = pick_thresholds(val.label.to_numpy(), risk)
    print("thresholds:", th)

    meta = {
        "model_version": f"tfidf-logreg-{dt.date.today().isoformat()}",
        "trained_on": dt.date.today().isoformat(),
        "C": best_c,
        "val_average_precision": round(best_ap, 4),
        "thresholds": th,
        "threshold_rule": f"suspicious: recall>={TARGET_RECALL} on val; scam: precision>={TARGET_PRECISION} on val",
        "sklearn_version": sklearn.__version__,  # the app warns if a different version loads the model
        "train_rows": int(len(train)),
        "train_sources": train.source.value_counts().to_dict(),
    }
    (MODELS / "baseline_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    model_module.load_meta.cache_clear()

    # Show the words/chunks the model relies on most (explainability + sanity check).
    feats = model.named_steps["features"].get_feature_names_out()
    coefs = model.named_steps["clf"].coef_[0]
    order = np.argsort(coefs)
    print("\nTop scam signals:", [feats[i] for i in order[-25:][::-1]])
    print("Top safe signals:", [feats[i] for i in order[:25]])


if __name__ == "__main__":
    main()
