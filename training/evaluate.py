"""Step 4: evaluate every model fairly and write reports/RESULTS.md.

Run:  python -m training.evaluate

Rules for a fair comparison
  * Every system is scored on the SAME test rows.
  * Every system's flag threshold is chosen on the VALIDATION set with the same
    rule (flag >= 97% of validation scams). The test set is touched once, at the end.
  * We report precision, recall, F1, false-positive rate (FPR) and
    false-negative rate (FNR), not just accuracy. With 1 scam per 5 messages, a
    model that says "safe" to everything is 80% "accurate" and useless.

Glossary
  precision = of the messages we flagged, how many really were scams
  recall    = of the real scams, how many we flagged          (= 1 - FNR)
  FPR       = of the safe messages, how many we wrongly flagged (false alarms)
  FNR       = of the real scams, how many we missed            (the dangerous error)
  AP        = average precision: area under the precision-recall curve,
              threshold-free summary (1.0 = perfect)
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, confusion_matrix, precision_recall_curve, roc_auc_score

from scam_detector.detector import check_message, score_texts, verdict_for
from scam_detector.model import load_meta
from training.train_baseline import TARGET_RECALL, build_pipeline, pick_thresholds

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
CHALLENGE = ROOT / "data" / "challenge" / "challenge_set.csv"
REPORTS = ROOT / "reports"
PREDS = REPORTS / "preds"
FIG = REPORTS / "figures"

# Reference categorical palette, fixed order (see docs/LEARNING_GUIDE.md, charts section).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]


def load() -> dict[str, pd.DataFrame]:
    d = {s: pd.read_csv(DATA / f"{s}.csv") for s in ("train", "val", "test")}
    ch = pd.read_csv(CHALLENGE)
    ch["label"] = (ch["label"] == "scam").astype(int)
    ch["source"] = "challenge"
    ch["category"] = ch["category"].fillna("none")
    d["challenge"] = ch
    return d


def flag_threshold(y_val: np.ndarray, s_val: np.ndarray) -> float:
    """Validation-tuned threshold: catch >= 97% of scams.

    If a system can never reach 97% recall without flagging everything (e.g.
    rules only), fall back to the threshold with the best F1 on validation.
    """
    t = pick_thresholds(y_val, s_val)["suspicious"]
    if t > 0:
        return t
    p, r, th = precision_recall_curve(y_val, s_val)
    f1 = 2 * p * r / np.maximum(p + r, 1e-9)
    return float(th[np.argmax(f1[:-1])])


def metrics(y: np.ndarray, s: np.ndarray, t: float) -> dict:
    pred = (s >= t).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    out = {
        "n": int(len(y)),
        "scams": int(y.sum()),
        "precision": round(prec, 3),
        "recall": round(rec, 3),
        "f1": round(f1, 3),
        "fpr": round(fp / (fp + tn), 3) if fp + tn else None,
        "fnr": round(fn / (fn + tp), 3) if fn + tp else None,
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
    }
    if 0 < y.sum() < len(y):
        out["ap"] = round(average_precision_score(y, s), 3)
        out["roc_auc"] = round(roc_auc_score(y, s), 3)
    return out


def system_scores(d: dict) -> tuple[dict, dict]:
    """Return {system: {split: scores}} and {system: info}."""
    scores: dict[str, dict] = {}
    info: dict[str, dict] = {}
    model = joblib.load(ROOT / "models" / "baseline.joblib")
    rules_cache = {s: np.array([x["rule_score"] for x in score_texts(d[s].text.tolist(), use_model=False)])
                   for s in ("val", "test", "challenge")}

    scores["Rules only"] = rules_cache
    info["Rules only"] = {"what": "hand-written red-flag rules + link checks", "size_mb": 0.03}

    base = {s: model.predict_proba(d[s].text)[:, 1] for s in ("val", "test", "challenge")}
    scores["TF-IDF + LogReg"] = base
    info["TF-IDF + LogReg"] = {"what": "word + character TF-IDF, logistic regression", "size_mb": 1.0}

    scores["TF-IDF + LogReg + rules (deployed)"] = {s: np.maximum(base[s], rules_cache[s]) for s in base}
    info["TF-IDF + LogReg + rules (deployed)"] = {"what": "max(model probability, rule score)", "size_mb": 1.0}

    for name, label in (("embed_minilm", "Multilingual MiniLM embeddings + LogReg"),
                        ("finetune_muril_base_cased", "MuRIL fine-tuned")):
        p = PREDS / f"{name}_test.csv"
        if not p.exists():
            continue
        sc = {s: pd.read_csv(PREDS / f"{name}_{s}.csv")["prob"].to_numpy() for s in ("val", "test", "challenge")}
        scores[label] = sc
        scores[label + " + rules"] = {s: np.maximum(sc[s], rules_cache[s]) for s in sc}
        meta = json.loads((PREDS / f"{name}_info.json").read_text())
        info[label] = {"what": meta.get("model"), "size_mb": meta.get("model_size_mb"), **meta}
        info[label + " + rules"] = {"what": "max(model probability, rule score)", "size_mb": meta.get("model_size_mb")}
    return scores, info


def timing(d: dict) -> dict:
    texts = d["test"].text.tolist()[:500]
    out = {}
    t0 = time.perf_counter()
    score_texts(texts, use_model=False)
    out["Rules only"] = 1000 * (time.perf_counter() - t0) / len(texts)
    model = joblib.load(ROOT / "models" / "baseline.joblib")
    t0 = time.perf_counter()
    for t in texts:
        model.predict_proba([t])
    out["TF-IDF + LogReg"] = 1000 * (time.perf_counter() - t0) / len(texts)
    t0 = time.perf_counter()
    for t in texts:
        check_message(t, online_link_check=False)
    out["Full check_message() (deployed)"] = 1000 * (time.perf_counter() - t0) / len(texts)
    return {k: round(v, 2) for k, v in out.items()}


def breakdown(df: pd.DataFrame, s: np.ndarray, t: float, col: str) -> pd.DataFrame:
    rows = []
    for key, idx in df.groupby(col).groups.items():
        idx = df.index.get_indexer(idx)
        m = metrics(df.label.to_numpy()[idx], s[idx], t)
        rows.append({col: key, "n": m["n"], "scams": m["scams"], "recall": m["recall"],
                     "FPR (false alarms)": m["fpr"], "precision": m["precision"]})
    return pd.DataFrame(rows).sort_values("n", ascending=False)


def cross_source(d: dict) -> pd.DataFrame:
    """Research experiment: does adding Indian data help on Indian-style messages?"""
    train = d["train"]
    setups = {
        "UCI only (English, UK/SG)": train[train.source == "uci"],
        "UCI + CloveAI (templated Indian)": train[train.source.isin(["uci", "clove"])],
        "UCI + CloveAI + synthetic Indian": train,
    }
    rows = []
    test = d["test"]
    for name, tr in setups.items():
        m = build_pipeline(10.0).fit(tr.text, tr.label)
        for eval_name, df in (
            ("synthetic Indian test", test[test.source == "synthetic"]),
            ("CloveAI test", test[test.source == "clove"]),
            ("UCI test", test[test.source == "uci"]),
            ("challenge set", d["challenge"]),
        ):
            p = m.predict_proba(df.text)[:, 1]
            r = metrics(df.label.to_numpy(), p, 0.5)
            rows.append({"trained on": name, "evaluated on": eval_name, "AP": r.get("ap"),
                         "recall@0.5": r["recall"], "FPR@0.5": r["fpr"]})
    return pd.DataFrame(rows)


def category_accuracy(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """When a scam is caught, is the scam TYPE we tell the user correct?"""
    rows = df[(df.label == 1) & (~df.category.isin(["unknown", "none", ""])) & df.category.notna()]
    preds = [check_message(t, online_link_check=False)["category"] for t in rows.text]
    rows = rows.assign(predicted=preds)
    caught = rows[rows.predicted.notna()]
    right = (caught.predicted == caught.category)
    confusions = (caught[~right].groupby(["category", "predicted"]).size().sort_values(ascending=False)
                  .head(8).reset_index(name="count").rename(columns={"category": "true type"}))
    return {"n_caught": int(len(caught)), "correct": int(right.sum()),
            "accuracy": round(float(right.mean()), 3) if len(caught) else None}, confusions


def plot_pr(d: dict, scores: dict, names: list[str]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 5), dpi=150)
    y = d["test"].label.to_numpy()
    for i, name in enumerate(names):
        p, r, _ = precision_recall_curve(y, scores[name]["test"])
        ax.plot(r, p, lw=2, color=SERIES[i], label=f"{name} (AP {average_precision_score(y, scores[name]['test']):.3f})")
    ax.set_xlabel("Recall (share of scams caught)")
    ax.set_ylabel("Precision (share of flags that were scams)")
    ax.set_title("Precision-recall on the test set", loc="left", fontsize=12)
    ax.set_xlim(0, 1.01)
    ax.set_ylim(0, 1.01)
    ax.grid(color="#e4e3df", lw=0.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="lower left", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "precision_recall.png")
    plt.close(fig)


def plot_confusion(cm: np.ndarray, title: str, path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list("blue", ["#f3f7fd", "#2a78d6"])
    fig, ax = plt.subplots(figsize=(4.6, 4), dpi=150)
    ax.imshow(cm, cmap=cmap)
    labels = ["safe", "scam"]
    ax.set_xticks([0, 1], [f"predicted\n{l}" for l in labels])
    ax.set_yticks([0, 1], [f"really\n{l}" for l in labels])
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{cm[i, j]}", ha="center", va="center", fontsize=14,
                    color="#0b0b0b" if cm[i, j] < cm.max() * 0.6 else "#ffffff")
    ax.set_title(title, loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def md_table(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    d = load()
    scores, info = system_scores(d)
    yv, yt, yc = (d[s].label.to_numpy() for s in ("val", "test", "challenge"))

    main_rows, ch_rows, results = [], [], {"systems": {}}
    for name, sc in scores.items():
        t = flag_threshold(yv, sc["val"])
        mt, mc = metrics(yt, sc["test"], t), metrics(yc, sc["challenge"], t)
        results["systems"][name] = {"threshold": t, "test": mt, "challenge": mc, "info": info.get(name, {})}
        main_rows.append({"system": name, "flag threshold": round(t, 3), "precision": mt["precision"],
                          "recall": mt["recall"], "F1": mt["f1"], "FPR": mt["fpr"], "FNR": mt["fnr"],
                          "AP": mt.get("ap"), "ROC-AUC": mt.get("roc_auc")})
        ch_rows.append({"system": name, "recall (scams caught)": mc["recall"], "FPR (false alarms)": mc["fpr"],
                        "missed scams": mc["fn"], "false alarms": mc["fp"]})

    # Deployed system details (uses the shipped thresholds from models/baseline_meta.json).
    deployed = "TF-IDF + LogReg + rules (deployed)"
    th = load_meta()["thresholds"]
    s_test = scores[deployed]["test"]
    t_flag = th["suspicious"]
    test = d["test"].copy()
    test["verdict"] = [verdict_for(r, th) for r in s_test]
    three_way = pd.crosstab(test.label.map({0: "really safe", 1: "really scam"}), test.verdict).reindex(
        columns=["scam", "suspicious", "likely_safe"], fill_value=0)
    cm = confusion_matrix(yt, (s_test >= t_flag).astype(int))
    plot_confusion(cm, "Deployed system, test set\n(flag = SCAM or SUSPICIOUS)", FIG / "confusion_matrix_test.png")

    by_source = breakdown(test.reset_index(drop=True), s_test, t_flag, "source")
    by_lang = breakdown(test.reset_index(drop=True), s_test, t_flag, "language")
    syn_scam = (test.label.to_numpy() == 1) & (test.source.to_numpy() == "synthetic")
    by_cat = breakdown(test[syn_scam].reset_index(drop=True), s_test[syn_scam], t_flag, "category")[
        ["category", "n", "recall"]]

    ch = d["challenge"].copy()
    s_ch = scores[deployed]["challenge"]
    ch["risk"] = np.round(s_ch, 3)
    ch["verdict"] = [verdict_for(r, th) for r in s_ch]
    ch["correct"] = np.where(ch.label == 1, ch.verdict != "likely_safe", ch.verdict == "likely_safe")
    ch_lang = breakdown(ch.reset_index(drop=True), s_ch, t_flag, "language")
    adv = ch[ch.tests.str.startswith("ADVERSARIAL")]
    hard = ch[ch.tests.str.startswith("HARD NEGATIVE")]
    errors = ch[~ch.correct][["text", "label", "verdict", "risk", "tests"]]
    errors["label"] = errors.label.map({1: "scam", 0: "safe"})

    # Fairness: false-alarm rate per language for EVERY system, at its own flag threshold.
    lang_groups = {"English": ["en"], "Hinglish": ["hinglish"], "Hindi": ["hi"],
                   "Other code-mixed": ["bn_en", "mr_en", "ta_en", "te_en"]}
    fair_rows = []
    safe_mask = test.label.to_numpy() == 0
    for name, sc in scores.items():
        t = results["systems"][name]["threshold"]
        row = {"system": name}
        for g, langs in lang_groups.items():
            m = safe_mask & test.language.isin(langs).to_numpy()
            row[f"{g} FPR (n={int(m.sum())})"] = round(float((sc["test"][m] >= t).mean()), 3) if m.sum() else None
        fair_rows.append(row)
    fairness = pd.DataFrame(fair_rows)

    cat_syn, conf_syn = category_accuracy(test[test.source == "synthetic"])
    cat_ch, conf_ch = category_accuracy(ch)
    xs = cross_source(d)
    speed = timing(d)
    names_for_plot = [n for n in scores if not n.endswith("+ rules") or n == deployed][:6]
    plot_pr(d, scores, names_for_plot)

    results.update({
        "deployed_thresholds": th,
        "three_way_test": three_way.to_dict(),
        "challenge_adversarial_caught": f"{int(adv.correct.sum())}/{len(adv)}",
        "challenge_hard_negatives_correct": f"{int(hard.correct.sum())}/{len(hard)}",
        "category_accuracy": {"synthetic_test": cat_syn, "challenge": cat_ch},
        "speed_ms_per_message_cpu": speed,
        "test_rows": int(len(test)),
    })
    (REPORTS / "results.json").write_text(json.dumps(results, indent=2, default=str))

    md = [
        "# Results (auto-generated by `python -m training.evaluate`)",
        "",
        "> **Read this first.** No real messages from Indian users were available. The test set mixes "
        "real English SMS from the UK/Singapore (UCI, ~2011), template-generated Indian SMS (CloveAI) and "
        "LLM-written Indian messages (synthetic). These numbers show how the models behave on *this* data. "
        "They are **not** an estimate of real-world accuracy for elderly users in India. That needs real, "
        "consented, anonymised messages (see docs/TIMELINE.md).",
        "",
        f"Test rows: {len(test)} ({int(yt.sum())} scam/spam). Challenge set: {len(ch)} hand-written cases "
        f"({int(yc.sum())} scams). Flag threshold for each system chosen on the validation set so that it "
        f"flags >= {int(TARGET_RECALL * 100)}% of validation scams.",
        "",
        "## 1. All systems, test set",
        "",
        md_table(pd.DataFrame(main_rows)),
        "",
        "![precision-recall](figures/precision_recall.png)",
        "",
        "## 2. All systems, hand-written challenge set (tricky cases, never used in training)",
        "",
        md_table(pd.DataFrame(ch_rows)),
        "",
        "## 3. Deployed system in detail",
        "",
        f"Thresholds (from validation): SUSPICIOUS >= {th['suspicious']}, SCAM >= {th['scam']}.",
        "",
        "Three-way verdicts on the test set:",
        "",
        three_way.reset_index().rename(columns={"label": ""}).to_markdown(index=False),
        "",
        "![confusion matrix](figures/confusion_matrix_test.png)",
        "",
        "### By data source (test)",
        "",
        md_table(by_source),
        "",
        "### By language (test). Check for unfair false alarms on Hindi/Hinglish",
        "",
        md_table(by_lang),
        "",
        "### False alarms by language, every system (genuine test messages only)",
        "",
        "Small n means large uncertainty: with 12 genuine Hindi messages, one error moves the rate by 8 points.",
        "",
        md_table(fairness),
        "",
        "### By scam category (synthetic test scams only, as other sources have no categories)",
        "",
        md_table(by_cat),
        "",
        "### Challenge set by language",
        "",
        md_table(ch_lang),
        "",
        f"Adversarial (disguised) scams caught: **{int(adv.correct.sum())}/{len(adv)}**. "
        f"Hard negatives (scary-looking genuine messages) correctly left green: **{int(hard.correct.sum())}/{len(hard)}**.",
        "",
        "### Every challenge-set mistake (error analysis)",
        "",
        md_table(errors) if len(errors) else "_none_",
        "",
        "### Is the scam TYPE we show correct? (only for scams that were caught)",
        "",
        f"- Synthetic test scams: **{cat_syn['correct']}/{cat_syn['n_caught']}** correct type "
        f"(accuracy {cat_syn['accuracy']}). Note: the synthetic set has only 7 types.",
        f"- Challenge-set scams: **{cat_ch['correct']}/{cat_ch['n_caught']}** correct type (accuracy {cat_ch['accuracy']}).",
        "",
        "Most common type mix-ups (synthetic test):",
        "",
        md_table(conf_syn) if len(conf_syn) else "_none_",
        "",
        "Most common type mix-ups (challenge set):",
        "",
        md_table(conf_ch) if len(conf_ch) else "_none_",
        "",
        "## 4. Research experiment: does Indian training data matter?",
        "",
        "Same TF-IDF + LogReg model (C=10), trained on growing data, threshold 0.5.",
        "",
        md_table(xs),
        "",
        "## 5. Speed (CPU, one message at a time, this machine)",
        "",
        md_table(pd.DataFrame([{"system": k, "ms per message": v} for k, v in speed.items()])),
        "",
        "Model details:",
        "",
    ]
    for name, inf in info.items():
        if not name.endswith("+ rules"):
            md.append(f"- **{name}**: " + ", ".join(f"{k}={v}" for k, v in inf.items() if k != "what") + f". {inf.get('what', '')}")
    (REPORTS / "RESULTS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:40]))


if __name__ == "__main__":
    main()
