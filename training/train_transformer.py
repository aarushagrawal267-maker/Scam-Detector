"""Step 3: the "advanced" models, for comparison with the baseline.

Two approaches:

  A. --mode embed    (fast, CPU-friendly)
     A pretrained multilingual sentence-embedding model turns each message into
     384 numbers that capture its meaning, in 50+ languages. We keep that model
     frozen and train a Logistic Regression on top.
     Model: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

  B. --mode finetune (slower; best on a GPU, e.g. free Google Colab)
     Fine-tune MuRIL, Google's BERT model trained on 17 Indian languages
     INCLUDING transliterated text (Hindi written in English letters), which is
     exactly what Hinglish scam messages look like.
     Model: google/muril-base-cased

Run:
    python -m training.train_transformer --mode embed
    python -m training.train_transformer --mode finetune --epochs 2
On Colab: Runtime > Change runtime type > T4 GPU, clone the repo, pip install
-r requirements-ml.txt, run the same command. It detects the GPU automatically.

Each run writes predicted probabilities for val / test / challenge sets to
reports/preds/<name>_<split>.csv, so training/evaluate.py can compare every
model with exactly the same metrics.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
CHALLENGE = ROOT / "data" / "challenge" / "challenge_set.csv"
PREDS = ROOT / "reports" / "preds"
SEED = 42


def load_splits() -> dict[str, pd.DataFrame]:
    splits = {s: pd.read_csv(DATA / f"{s}.csv") for s in ("train", "val", "test")}
    ch = pd.read_csv(CHALLENGE)
    ch["label"] = (ch["label"] == "scam").astype(int)
    splits["challenge"] = ch
    return splits


def save_preds(name: str, splits: dict, probs: dict, info: dict) -> None:
    PREDS.mkdir(parents=True, exist_ok=True)
    for split, p in probs.items():
        pd.DataFrame({"label": splits[split]["label"], "prob": p}).to_csv(
            PREDS / f"{name}_{split}.csv", index=False
        )
    (PREDS / f"{name}_info.json").write_text(json.dumps(info, indent=2))


def run_embed(splits: dict) -> None:
    from sentence_transformers import SentenceTransformer
    from sklearn.linear_model import LogisticRegression

    model_id = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    enc = SentenceTransformer(model_id, device="cpu")
    emb = {}
    t0 = time.time()
    for s, df in splits.items():
        emb[s] = enc.encode(df.text.tolist(), batch_size=64, show_progress_bar=False, normalize_embeddings=True)
    encode_secs = time.time() - t0
    n_total = sum(len(df) for df in splits.values())

    best = None
    from sklearn.metrics import average_precision_score

    for C in (0.3, 1, 3, 10, 30):
        clf = LogisticRegression(C=C, class_weight="balanced", max_iter=5000).fit(emb["train"], splits["train"].label)
        ap = average_precision_score(splits["val"].label, clf.predict_proba(emb["val"])[:, 1])
        if best is None or ap > best[0]:
            best = (ap, C, clf)
    ap, C, clf = best
    probs = {s: clf.predict_proba(emb[s])[:, 1] for s in ("val", "test", "challenge")}
    save_preds(
        "embed_minilm",
        splits,
        probs,
        {
            "model": model_id + " (frozen) + LogisticRegression",
            "C": C,
            "val_average_precision": round(float(ap), 4),
            "ms_per_message_cpu": round(1000 * encode_secs / n_total, 2),
            "model_size_mb": 471,
        },
    )
    print(f"embed: C={C} val AP={ap:.4f}, {1000 * encode_secs / n_total:.1f} ms/message")


def run_finetune(splits: dict, epochs: int, max_len: int, model_id: str, train_limit: int | None) -> None:
    import torch
    from torch.utils.data import DataLoader
    from transformers import AutoModelForSequenceClassification, AutoTokenizer, DataCollatorWithPadding, get_linear_schedule_with_warmup

    torch.manual_seed(SEED)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.set_num_threads(max(1, torch.get_num_threads()))
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSequenceClassification.from_pretrained(model_id, num_labels=2).to(device)

    train = splits["train"].sample(frac=1, random_state=SEED)
    if train_limit:
        train = train.groupby("label", group_keys=False).apply(
            lambda g: g.sample(min(len(g), train_limit // 2), random_state=SEED)
        )

    def encode(df: pd.DataFrame, with_labels: bool = True):
        enc = tok(df.text.tolist(), truncation=True, max_length=max_len)
        items = [{k: enc[k][i] for k in enc} for i in range(len(df))]
        if with_labels:
            for it, y in zip(items, df.label.tolist()):
                it["labels"] = int(y)
        return items

    collate = DataCollatorWithPadding(tok)
    # Sort by length inside the loader for speed? Keep simple: shuffle.
    train_loader = DataLoader(encode(train), batch_size=16, shuffle=True, collate_fn=collate)

    # Class weights: scams are rarer, so their errors cost more (same idea as class_weight="balanced").
    pos = train.label.mean()
    weights = torch.tensor([0.5 / (1 - pos), 0.5 / pos], dtype=torch.float, device=device)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weights)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-5, weight_decay=0.01)
    steps = epochs * len(train_loader)
    sched = get_linear_schedule_with_warmup(opt, int(0.06 * steps), steps)

    t0 = time.time()
    model.train()
    step = 0
    for epoch in range(epochs):
        for batch in train_loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            labels = batch.pop("labels")
            loss = loss_fn(model(**batch).logits, labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            step += 1
            if step % 50 == 0:
                print(f"epoch {epoch + 1} step {step}/{steps} loss {loss.item():.4f} ({time.time() - t0:.0f}s)", flush=True)
    train_secs = time.time() - t0

    @torch.no_grad()
    def predict(df: pd.DataFrame) -> np.ndarray:
        model.eval()
        out = []
        loader = DataLoader(encode(df, with_labels=False), batch_size=64, collate_fn=collate)
        for batch in loader:
            batch = {k: v.to(device) for k, v in batch.items()}
            out.append(torch.softmax(model(**batch).logits, -1)[:, 1].cpu().numpy())
        return np.concatenate(out)

    t1 = time.time()
    probs = {s: predict(splits[s]) for s in ("val", "test", "challenge")}
    n_pred = sum(len(splits[s]) for s in ("val", "test", "challenge"))
    infer_ms = 1000 * (time.time() - t1) / n_pred

    from sklearn.metrics import average_precision_score

    name = "finetune_" + model_id.split("/")[-1].replace("-", "_")
    save_preds(
        name,
        splits,
        probs,
        {
            "model": model_id + " fine-tuned",
            "epochs": epochs,
            "max_len": max_len,
            "train_rows": int(len(train)),
            "device": device,
            "train_minutes": round(train_secs / 60, 1),
            "val_average_precision": round(float(average_precision_score(splits["val"].label, probs["val"])), 4),
            "ms_per_message": round(infer_ms, 2),
            "model_size_mb": 950,
        },
    )
    print(f"done: {name}, train {train_secs / 60:.1f} min, {infer_ms:.1f} ms/message on {device}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["embed", "finetune"], required=True)
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--max-len", type=int, default=128)
    ap.add_argument("--model", default="google/muril-base-cased")
    ap.add_argument("--train-limit", type=int, default=None, help="cap training rows (for slow CPUs)")
    args = ap.parse_args()
    splits = load_splits()
    if args.mode == "embed":
        run_embed(splits)
    else:
        run_finetune(splits, args.epochs, args.max_len, args.model, args.train_limit)


if __name__ == "__main__":
    main()
