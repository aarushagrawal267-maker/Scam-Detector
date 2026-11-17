# Model card: deployed scam detector

*Version `tfidf-logreg-2026-11-17`. Files: `models/baseline.joblib`, `models/baseline_meta.json`.*

## What it is
A hybrid of:
1. **TF-IDF + logistic regression** (scikit-learn): word 1–2-grams (≤ 50k) + character 2–5-grams (≤ 150k), `C = 10`, `class_weight="balanced"`; and
2. **22 hand-written red-flag rules** + offline link checks (`scam_detector/rules.py`, `urls.py`).

`risk = max(model probability, rule score)`; 🔴 SCAM if risk ≥ 0.6512, 🟡 SUSPICIOUS if ≥ 0.3373, else 🟢 LIKELY SAFE. Thresholds chosen on validation: yellow catches ≥ 97% of validation scams; red is ≥ 97% precise on validation.

## Intended use
A **second opinion** for individuals, especially older adults in India, about a single SMS/WhatsApp message, with plain-language reasons and pointers to official help (1930, cybercrime.gov.in, Chakshu).

**Not intended for:** automatic blocking or deleting of messages; judging people or phone numbers; legal or financial decisions; any use where a 🟢 result would be treated as proof of safety.

## Training data
5,797 messages: UCI SMS Spam (real, English, UK/Singapore, ~2011), CloveAI india-spam-sms (template-generated, capped at 15 per template), Ridham115 synthetic Indian scams (LLM-written, multilingual). **No real messages from Indian users.** See `DATA_CARD.md`.

## Evaluation (test set: 1,161 messages, 294 scams; full details in `reports/RESULTS.md`)

| Metric | Value |
|---|---|
| Recall (scams flagged 🔴 or 🟡) | 0.966 |
| Precision | 0.902 |
| False-positive rate | 0.036 |
| False-negative rate | 0.034 |
| Average precision / ROC-AUC | 0.988 / 0.993 |
| Challenge set (70 hand-written) | 33/38 scams caught, 0/32 false alarms |
| Disguised (adversarial) scams | 4/9 caught |
| Speed / size | ~2 ms per message (CPU) / 1 MB |

### By language (false-alarm rate on genuine messages, test)
English 0.9% · Hinglish 20% · Hindi 25% (12 genuine Hindi messages only) · other code-mixed 8–50% (very small samples).

## Known limitations and risks
- **Unknown real-world accuracy**: no real Indian user data yet.
- **Unequal false alarms**: Hindi/Hinglish users get many more false 🟡 warnings than English users.
- **Shortcut features** learned from data quirks: `http` vs `https`, British SMS words, Devanagari characters.
- **Disguised scams** (paraphrased OTP/CVV requests) are often missed.
- **Scam type** is right only about half the time on synthetic data (often "type unclear").
- **Rules** encode one author's assumptions and were revised once after validation error analysis.
- **Over-trust**: users might treat 🟢 as "safe". Every reply carries a disclaimer and never uses the word "safe" alone.

## Ethical considerations
No message text is stored. Anonymous counts only (see `PRIVACY_POLICY.md`). The tool complements, and must never replace, official reporting channels.

## How to reproduce
```bash
python -m training.prepare_data && python -m training.train_baseline && python -m training.evaluate
```
