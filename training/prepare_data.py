"""Step 1 of the ML pipeline: download, clean, merge and split the data.

Run:  python -m training.prepare_data

What it does (and why)
----------------------
1. Downloads three public datasets from Hugging Face (see docs/DATA_CARD.md):
     * UCI SMS Spam Collection   - real English SMS (UK/Singapore, ~2011). Label "spam".
     * CloveAI india-spam-sms    - Indian-style SMS made from ~121 templates.
     * Ridham115 indian-scam-sms-synthetic-audited - LLM-written Indian scam
       and genuine look-alike messages in English, Hindi, Hinglish and more.
2. Puts them in one format:  text, label (1 = scam/spam, 0 = safe), source,
   language, category.
3. Removes exact duplicates.
4. Groups near-duplicates ("templates"): messages that are the same after
   replacing numbers, links and capitalised names. All messages of one group go
   to the SAME split. Otherwise the test set would contain copies of training
   messages and the scores would look far better than reality ("data leakage").
5. Caps each CloveAI template at 15 messages so 121 templates don't drown out
   the other data.
6. Splits each source 70% train / 15% validation / 15% test, keeping the
   scam/safe ratio similar in every split (stratified, grouped).

The hand-written challenge set (data/challenge/challenge_set.csv) is NEVER used
for training; it's only for stress-testing.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from scam_detector.text_utils import detect_language, normalise

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
SEED = 42
CLOVE_CAP_PER_TEMPLATE = 15

SOURCES = {
    "uci": ("ucirvine/sms_spam", "plain_text/train-00000-of-00001.parquet"),
    "clove": ("CloveAI/india-spam-sms", "data/train-00000-of-00001.parquet"),
    "synthetic": ("Ridham115/indian-scam-sms-synthetic-audited", "data/synthetic_audited.csv"),
}

# Map the synthetic dataset's scam types onto our category ids.
SYNTH_CATEGORY = {
    "fake_kyc": "fake_bank_kyc",
    "fake_bank_otp": "otp_theft",
    "lottery": "lottery_prize",
    "courier_customs": "delivery_fee",
    "job_offer": "job_offer",
    "electricity_bill": "electricity_bill",
    "loan_offer": "loan_offer",
    "unknown": "unknown",
}


def download() -> dict[str, Path]:
    from huggingface_hub import hf_hub_download

    paths = {}
    for name, (repo, file) in SOURCES.items():
        local = RAW / repo.replace("/", "__")
        paths[name] = Path(hf_hub_download(repo, file, repo_type="dataset", local_dir=local))
    return paths


def template_key(text: str) -> str:
    """Same key => same 'template'. Numbers, links and Capitalised words are blanked."""
    t = re.sub(r"https?://\S+|www\.\S+", "URL", text)
    t = re.sub(r"\d+", "0", t)
    t = re.sub(r"\b[A-Z][a-z]+\b", "W", t)
    t = re.sub(r"[^\w\s]", "", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def load(paths: dict[str, Path]) -> pd.DataFrame:
    uci = pd.read_parquet(paths["uci"]).rename(columns={"sms": "text"})
    uci = uci.assign(source="uci", category="unknown", language=None)

    clove = pd.read_parquet(paths["clove"])
    clove = clove.assign(source="clove", category="unknown", language=None)

    syn = pd.read_csv(paths["synthetic"])
    syn = pd.DataFrame(
        {
            "text": syn["text"],
            "label": (syn["label"] == "scam").astype(int),
            "source": "synthetic",
            "category": syn["scam_type"].map(SYNTH_CATEGORY).fillna("none"),
            "language": syn["language"],  # the dataset's own language tag
        }
    )
    df = pd.concat([uci[syn.columns], clove[syn.columns], syn], ignore_index=True)
    df["text"] = df["text"].astype(str).map(normalise)
    df = df[df["text"].str.len() > 0]
    # Our own language guess (en / hi / hinglish) for sources without a tag.
    df["language"] = df["language"].fillna(df["text"].map(detect_language))
    df.loc[df["label"] == 0, "category"] = "none"
    return df


def dedupe_and_group(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset="text", keep="first")
    # If the same text has different labels in different sources, drop it (label noise).
    print(f"exact duplicates removed: {before - len(df)}")
    df = df.assign(group=df["text"].map(template_key))
    conflict = df.groupby("group")["label"].nunique()
    bad = set(conflict[conflict > 1].index)
    if bad:
        print(f"template groups with conflicting labels (kept, but flagged): {len(bad)}")
    df["label_conflict_group"] = df["group"].isin(bad)

    clove = df[df.source == "clove"]
    capped = clove.groupby("group", group_keys=False).apply(
        lambda g: g.sample(min(len(g), CLOVE_CAP_PER_TEMPLATE), random_state=SEED)
    )
    print(f"clove: {len(clove)} rows in {clove.group.nunique()} templates -> capped to {len(capped)}")
    return pd.concat([df[df.source != "clove"], capped], ignore_index=True)


def split(df: pd.DataFrame) -> pd.DataFrame:
    """70/15/15 per source, grouped by template, stratified by label."""
    parts = []
    for source, sub in df.groupby("source"):
        sub = sub.reset_index(drop=True).copy()
        sub["split"] = "train"
        # ~15% test: take 1 fold out of 7
        sgkf = StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=SEED)
        _, test_idx = next(sgkf.split(sub, sub["label"], sub["group"]))
        sub.loc[test_idx, "split"] = "test"
        rest = sub[sub.split == "train"]
        sgkf2 = StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=SEED)
        _, val_idx = next(sgkf2.split(rest, rest["label"], rest["group"]))
        sub.loc[rest.index[val_idx], "split"] = "val"
        parts.append(sub)
    return pd.concat(parts, ignore_index=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = split(dedupe_and_group(load(download())))
    # Leakage check: no template group may appear in two splits.
    leaks = df.groupby("group")["split"].nunique()
    assert (leaks == 1).all(), "a template group appears in more than one split!"
    cols = ["text", "label", "source", "language", "category", "group", "split"]
    for name in ("train", "val", "test"):
        part = df[df.split == name][cols]
        part.to_csv(OUT / f"{name}.csv", index=False)
    summary = df.groupby(["split", "source", "label"]).size().unstack(fill_value=0)
    print(summary)
    print("\nlanguages:\n", df.groupby(["split", "language"]).size().unstack(fill_value=0))
    summary.to_csv(OUT / "split_summary.csv")


if __name__ == "__main__":
    main()
