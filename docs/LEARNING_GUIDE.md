# Learning Guide: everything you need to know about this project

This guide explains **every part** of the AI Scam Message Detector: what it does, why it was built that way, the maths behind it, the honest results, and how to defend it in an interview. Read it in order. Each part ends with a short quiz; answers are at the very end.

> **Honesty first.** The first version of this code was generated with an AI assistant on 17 Nov 2026. That is allowed, and it is now *your* project, but only once you understand it. Judges and interviewers will ask "why did you choose X?" The answers are all in here. Whenever you describe the project, say plainly that the first version was AI-assisted, and point to what you did yourself: real data, user testing, improvements. Check each competition's current rules on AI-tool disclosure.

---

## Contents

1. [The big picture](#1-the-big-picture)
2. [Project map: every file](#2-project-map-every-file)
3. [How to run everything](#3-how-to-run-everything)
4. [Data: where it came from and its traps](#4-data)
5. [Turning text into numbers: TF-IDF](#5-tf-idf)
6. [The baseline model: logistic regression](#6-logistic-regression)
7. [Measuring a model: confusion matrix, precision, recall](#7-metrics)
8. [Thresholds: why missing a scam is worse than a false alarm](#8-thresholds)
9. [Red-flag rules](#9-rules)
10. [Link checking](#10-links)
11. [Combining model + rules into a verdict](#11-hybrid)
12. [Advanced models: embeddings and MuRIL](#12-transformers)
13. [The results and what they mean](#13-results)
14. [Screenshots (OCR)](#14-ocr)
15. [The website and API](#15-web)
16. [The Telegram bot](#16-bot)
17. [Privacy and security by design](#17-privacy)
18. [Designing for elderly users](#18-ux)
19. [Testing](#19-testing)
20. [Limitations: say these before anyone asks](#20-limitations)
21. [Interview questions with answers](#21-interview)
22. [Glossary](#22-glossary)
23. [Quiz answers](#23-answers)

---

## 1. The big picture

A person forwards a suspicious message. Within about **2 milliseconds** of computing time the system replies:

```
🔴 SCAM - Fake bank / KYC alert
• It asks you to update KYC, PAN or Aadhaar from a message...
• It threatens that your account, card or SIM will be blocked.
👉 Banks never ask you to update KYC through an SMS or WhatsApp link.
ℹ️ This is an automatic check and it can be wrong.
```

The journey of one message (`scam_detector/detector.py → check_message`):

```
message text (or text read from a screenshot by OCR)
   │
   ├─1─ clean it up (normalise) + guess language (en / hi / hinglish)
   ├─2─ find links → score each link WITHOUT opening it (urls.py)
   ├─3─ red-flag rules: OTP request? threat? prize? ... (rules.py)  → rule score 0..1
   ├─4─ ML model: TF-IDF + logistic regression (model.py)            → probability 0..1
   │
   ├─5─ risk = max(rule score, model probability)
   ├─6─ risk ≥ 0.651 → 🔴 SCAM | risk ≥ 0.337 → 🟡 SUSPICIOUS | else 🟢 LIKELY SAFE
   └─7─ build reply: verdict word + emoji, scam type, top reasons, what to do, disclaimer
```

Why two detectors (rules + ML)? Each covers the other's weakness:
- The **ML model** learns patterns from thousands of examples, including ones nobody thought to write a rule for. But it can't explain itself, and it only knows what was in its training data.
- The **rules** explain themselves in plain words ("it asks for your OTP") and catch scam tricks even when the training data had few examples. But they only catch what someone wrote a rule for.

### Quiz 1
1. In what order does `check_message` do its steps, and which step produces the words the user reads?
2. Why does the system use both rules and a model instead of just one?
3. Why is the green verdict called "LIKELY SAFE" and never "SAFE"?

---

## 2. Project map: every file

| Path | What it does | Key idea |
|---|---|---|
| `scam_detector/text_utils.py` | Cleans text, detects language, finds links/phone numbers, defangs links, anonymises personal data | Unicode NFKC normalisation; Devanagari Unicode range `U+0900–U+097F`; Hinglish marker words |
| `scam_detector/urls.py` | Scores links: look-alike brands, shorteners, risky endings, IP addresses, `.apk`, punycode; optional Google Safe Browsing | We **never** open a link |
| `scam_detector/rules.py` | 22 red-flag rules (regular expressions) in English/Hinglish/Hindi, negation handling, safe signals, noisy-OR scoring, category voting | Explainability |
| `scam_detector/model.py` | Loads the trained model file and returns probabilities | Only load model files you trained yourself |
| `scam_detector/detector.py` | Combines everything into a verdict + reply | `risk = max(model, rules)` |
| `scam_detector/messages.py` | Every sentence the user reads, in English and Hindi | Plain words, ≤ 5-line replies |
| `scam_detector/stats.py` | Anonymous counters for the dashboard (SQLite) | Counts only, never text |
| `scam_detector/ocr.py` | Reads text from screenshots using Tesseract | Image processed in memory, never saved |
| `training/prepare_data.py` | Downloads, cleans, de-duplicates and splits the data | Template grouping prevents data leakage |
| `training/train_baseline.py` | Trains TF-IDF + logistic regression; picks C and thresholds on validation data | Validation set for choices, test set only at the end |
| `training/train_transformer.py` | MiniLM embeddings + LogReg, and MuRIL fine-tuning | Fair comparison with the baseline |
| `training/evaluate.py` | Scores every system the same way and writes `reports/RESULTS.md` | Per language, per source, per type, challenge set |
| `app/server.py` | FastAPI web server: website + JSON API | Rate limit, security headers, no logging of text |
| `app/static/*` | The website (HTML/CSS/JavaScript) | Large text, high contrast, bilingual |
| `bot/telegram_bot.py` | The Telegram chat bot | Logic separated from network so it can be tested |
| `tests/` | 36 automated tests | Includes a privacy test and upload-limit tests |
| `data/challenge/challenge_set.csv` | 70 hand-written tricky test cases | Never used for training |
| `models/baseline.joblib`, `baseline_meta.json` | The trained model (1 MB) and its thresholds | |
| `reports/RESULTS.md`, `reports/figures/` | All results, generated automatically | |
| `docs/` | Everything else: data card, model card, paper draft, pilot protocol, privacy policy, outreach plan... | |

---

## 3. How to run everything

```bash
python -m venv .venv
```
```bash
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```
```bash
pip install -r requirements.txt -r requirements-ml.txt -r requirements-dev.txt
```
```bash
python -m pytest                  # 36 tests should pass
```
```bash
python -m training.prepare_data   # download + split data (~1 min)
```
```bash
python -m training.train_baseline # train the model (~20 s)
```
```bash
python -m training.train_transformer --mode embed   # optional, ~2 min
```
```bash
python -m training.evaluate       # writes reports/RESULTS.md
```
```bash
uvicorn app.server:app --reload   # website at http://127.0.0.1:8000
```
```bash
TELEGRAM_BOT_TOKEN=... python -m bot.telegram_bot   # chat bot
```

A **virtual environment** (`.venv`) is a private folder of Python packages for this project, so versions don't clash with other projects. `requirements.txt` pins exact versions so the project works the same on every computer. The scikit-learn version especially must match the one the model was trained with.

---

## 4. Data

### 4.1 The three datasets (details in `docs/DATA_CARD.md`)

| Dataset | Real? | Indian? | Size used | Its trap |
|---|---|---|---|---|
| UCI SMS Spam Collection | ✅ real | ❌ UK/Singapore, ~2011 | 5,105 | "spam" includes marketing, not just scams; British words become shortcuts |
| CloveAI india-spam-sms | ❌ template-generated | ✅ | 1,378 (from 20,010) | Only ~121 templates! |
| Ridham115 synthetic, audited | ❌ written by AI models | ✅ multilingual | 1,580 | Synthetic: AI-written scams may not look like real ones |

**Spam ≠ scam.** "50% off sarees this Diwali!" is spam (unwanted marketing) but not a scam (it isn't trying to steal from you). UCI labels both as spam. Our challenge set labels a genuine promotion as *safe*. This mismatch is a known limitation.

### 4.2 Data leakage: the trap that makes results look fake-good

CloveAI has 20,010 rows, but after replacing numbers and names, only **121 different templates** remain:
```
"Your debit card XXHDFC has been blocked. Call ..."
"Your debit card XXSBI has been blocked. Call ..."     ← same template
```
If you split randomly, copies of the same template land in both training and test. The model has effectively *seen the exam answers*, and scores near 100%. That is **data leakage**.

**Fix (`prepare_data.py`)**: compute a *template key* for every message (numbers → `0`, links → `URL`, Capitalised words → `W`). All messages with the same key form a **group**, and a group goes entirely into train, or entirely into validation, or entirely into test. The script asserts this, so it would crash if a group crossed splits. We also **cap** each CloveAI template at 15 messages so 121 templates don't drown out everything else.

Evidence that this mattered: in the cross-dataset experiment (§13), a model trained with CloveAI scores a perfect **1.000** on CloveAI's test set but catches only **26%** of the challenge-set scams. Perfect scores on templated data mean nothing.

### 4.3 Train / validation / test

| Split | Share | Used for |
|---|---|---|
| **Train** (5,797) | 70% | The model learns from these |
| **Validation** (1,160) | 15% | Every *choice* we make: C, thresholds, which rules to soften |
| **Test** (1,161) | 15% | Final score, looked at **once** at the end |

Analogy: train = homework, validation = practice tests, test = the final exam. If you keep tweaking until the final-exam score looks good, the final exam has become practice, and the score is no longer honest.

**Stratified** means each split keeps the same scam/safe ratio. The split is done **per source** so each split has UCI, CloveAI and synthetic data in the same proportions.

### 4.4 The challenge set
70 hand-written cases (`data/challenge/challenge_set.csv`) designed to be hard:
- **adversarial scams**: "acc0unt wi11 be b1ocked", "share the O.T.P", "tell me the 3 digit number on the back of your card";
- **hard negatives**: genuine messages that *look* scary: real OTP messages ("Do not share this OTP"), real KYC reminders sending you to the branch, a real power-cut notice.

It is never used to train or tune, so it acts as a stress test.

### Quiz 4
1. Why would a random split of CloveAI give a misleadingly high score?
2. You tried 5 values of C and picked the best. Which split did you use to pick it, and why not the test split?
3. Give one example of a message that is spam but not a scam.

---

## 5. TF-IDF

A model needs numbers, not words. **TF-IDF** turns each message into a long list of numbers, one per word (or letter-chunk) in the vocabulary.

- **TF (term frequency)**: how often a term appears in *this* message. (We use `sublinear_tf`: 1 + log(count), so saying "urgent" 5 times doesn't count 5×.)
- **IDF (inverse document frequency)**: how *rare* the term is across all messages. `idf = log((1 + N) / (1 + df)) + 1`, where N = number of messages and df = number of messages containing the term. "the" appears everywhere → low IDF. "kyc" is rare → high IDF.
- TF × IDF, then each message's vector is scaled to length 1.

**Tiny example.** Three messages: (1) "update kyc now", (2) "see you now", (3) "kyc done". "now" appears in 2 of 3 messages, "kyc" in 2 of 3, "update" in only 1 → "update" gets the highest weight in message 1.

**Two kinds of features (`train_baseline.py`):**
- **Word n-grams (1–2 words):** "click", "click here", "kyc update".
- **Character n-grams (2–5 letters, inside word boundaries):** "acc0unt" shares chunks like "acc", "unt" with "account". "jayega" and "jaega" share "ja", "ega". This is why a simple model copes with **Hinglish spelling variation, typos and leetspeak**.

Vocabulary limits: 50,000 word features + 150,000 character features; terms seen in fewer than 2 messages are ignored (`min_df=2`).

---

## 6. Logistic regression

Each feature gets a **weight** (positive = scam-like, negative = safe-like). For a message:

```
score = w1·x1 + w2·x2 + ... + b
probability of scam = 1 / (1 + e^(−score))      ← the "sigmoid", squashes any number into 0..1
```

Training adjusts the weights to make the probabilities match the true labels as closely as possible (it minimises "log loss").

**C (regularisation).** Without limits, the model could memorise training messages with huge weights. Regularisation penalises big weights. **Small C = strong penalty** (simpler model), **large C = weak penalty**. We tried C = 0.3, 1, 3, 10, 30 and picked **C = 10**, which had the best validation average precision (0.9905).

**class_weight="balanced".** Only ~25% of training messages are scams. Without balancing, the model can get a low error by leaning towards "safe". Balancing makes each scam count more, about 3×.

**Explainability check.** After training, `train_baseline.py` prints the strongest features. Some are sensible ("otp", "verify", "claim", "fee", "won"). Some are **shortcuts**, which reveal dataset problems:
- "http" = scam, "https www" = safe: in the templated CloveAI data, scam templates used `http://` and genuine ones `https://`. Real scammers use https too.
- "uk", "txt": British words from the UCI data.
- A single Devanagari letter "र" as a scam signal → the model partly learned "Hindi = scam" from imbalanced data, which is part of why Hindi false alarms are higher (§13).

This is a strong point to raise in interviews: *"I looked at what my model learned, and found shortcuts."*

### Quiz 6
1. What does the sigmoid function do, and why is it needed?
2. If you increase C from 10 to 1000, what risk increases?
3. Why is "http" being a top scam signal a problem rather than a success?

---

## 7. Metrics

Every prediction falls into one of four boxes (the **confusion matrix**). Our deployed system on the 1,161 test messages, where "flagged" = 🔴 or 🟡:

|  | Flagged | Not flagged |
|---|---|---|
| **Really scam (294)** | TP = 284 ✅ | **FN = 10** ❌ missed scams |
| **Really safe (867)** | FP = 33 ⚠️ false alarms | TN = 834 ✅ |

| Metric | Formula | Our value | Plain meaning |
|---|---|---|---|
| **Precision** | TP / (TP + FP) | 284/317 = **0.896** | When we warn, we're right 90% of the time |
| **Recall** | TP / (TP + FN) | 284/294 = **0.966** | We catch 96.6% of scams |
| **FNR** | FN / (FN + TP) | **0.034** | We miss 3.4% of scams (the dangerous error) |
| **FPR** | FP / (FP + TN) | 33/867 = **0.038** | 3.8% of safe messages get a false warning |
| **F1** | 2·P·R / (P + R) | **0.930** | One number balancing precision and recall |
| Accuracy | (TP + TN) / all | 0.963 | Misleading here, see below |

**Why not just accuracy?** A useless "model" that says *safe* to everything scores 867/1161 = **74.7% accuracy** while catching **zero** scams. Accuracy hides the error that matters.

**Threshold-free metrics:**
- **Average precision (AP)**: area under the precision-recall curve (1.0 is perfect). Ours: 0.987.
- **ROC-AUC**: the chance that a random scam gets a higher score than a random safe message. Ours: 0.993.

### Quiz 7
1. Using the table above, compute precision if FP had been 100 instead of 33.
2. Which number would you quote to say "we miss few scams"? Which for "we rarely cry wolf"?
3. Why is accuracy misleading for this problem?

---

## 8. Thresholds

The model gives a probability. **We** decide where to draw the line. Lower threshold → catch more scams (recall ↑) but more false alarms (precision ↓). There's always a trade-off.

**Why we favour recall:** a missed scam (FN) can cost an elderly person their life savings. A false alarm (FP) costs them a phone call to their bank to double-check. The errors are not equally bad, so the threshold is not 0.5.

**Two thresholds → three verdicts**, both chosen on the **validation** set (`pick_thresholds` in `train_baseline.py`):
- **SUSPICIOUS ≥ 0.343**: the highest threshold that still flags **≥ 97%** of validation scams (high recall).
- **SCAM ≥ 0.631**: the lowest threshold where **≥ 97%** of messages above it are really scams (high precision), so a red verdict is rarely wrong.
- Below 0.343 → **LIKELY SAFE**.

Result on test: of 294 scams, **272 got 🔴, 12 got 🟡, 10 were missed (🟢)**. Of 867 safe messages, 834 got 🟢, 24 got 🟡 and 9 got 🔴.

The yellow band is a design choice for honesty: when the system is unsure, it says so instead of guessing.

### Quiz 8
1. Why is the SUSPICIOUS threshold chosen by recall but the SCAM threshold by precision?
2. What would happen to false alarms if you set SUSPICIOUS to 0.1?
3. Why must thresholds be chosen on validation data and not test data?

---

## 9. Rules

### 9.1 Regular expressions in 60 seconds
A **regular expression (regex)** is a pattern for text. Examples from `rules.py`:
- `\b(otp|pin|cvv)\b`: the whole word otp, pin or cvv (`\b` = word boundary, `|` = or).
- `[^.!?\n]{0,40}`: up to 40 characters that are not the end of a sentence, i.e. "within the same sentence".
- So `share[^.!?\n]{0,40}\botp\b` matches "share the OTP you received" but not "share. ... OTP" across sentences.

Hindi patterns don't use `\b`, because Hindi vowel signs (matras) confuse Python's idea of a "word character".

### 9.2 The 22 rules
Each rule has an id, a **weight** (0–1), and the scam types it points to. The strongest: `pin_to_receive_money` (0.7: "enter UPI PIN to receive money", which is never true), `asks_for_otp` (0.65), `remote_access_app` (0.6: AnyDesk etc.), `authority_threat` (0.55: police/CBI/"digital arrest"). Weaker ones like `urgency` (0.25) or `click_link` (0.15) only matter in combination.

### 9.3 Negation
"Do not share this OTP with anyone" contains "share ... OTP" but is a *safe* sign. For `asks_for_otp` and `asks_for_bank_details`, a match is ignored if the 30 characters before it contain "do not / don't / never / mat / न करें...".

### 9.4 Combining rules: noisy-OR
```
rule score = 1 − (1 − w1)(1 − w2)(1 − w3)...
```
Think of each rule as an independent "chance" the message is a scam. Example: urgency (0.25) + account threat (0.4) + KYC (0.25):
1 − (0.75 × 0.6 × 0.75) = 1 − 0.3375 = **0.66** → above 0.651 → 🔴. Each alone stays below the SCAM line, but together they cross it. Score can never exceed 1.

### 9.5 Safe signals (and how they came from error analysis)
The first evaluation showed **42% of genuine Hindi messages** and **29% of genuine synthetic messages** got false alarms. Looking at the **validation** errors (never the test) showed the cause: messages that merely *mentioned* KYC ("please visit your nearest branch to complete re-KYC") triggered the KYC rule (weight 0.45). Fixes:
1. KYC alone lowered to 0.25. It's only strong combined with a link, threat or demand.
2. "Safe signals" ("visit your nearest branch", "official app", "successfully updated", "do not share") **halve** the rule score...
3. ...but **never** when the message also asks for an OTP/PIN, a remote-access app, threatens arrest, or has a dangerous link, because scammers can copy polite phrases.

Effect on test (measured at the time, before the November 2026 fix to the CloveAI split): overall false alarms 4.5% → 3.6%, Hindi 42% → 25%, challenge-set false alarms 3 → 0, with recall unchanged. Report this honestly in your paper as "rules were revised once after validation error analysis".

### 9.6 Scam type
Each fired rule votes for its types with its weight; the highest total wins (ties broken by a priority list: the most dangerous types first). If no type-specific rule fired but the model flagged the message → "Type unclear".

### Quiz 9
1. Compute the rule score for `asks_for_otp` (0.65) + `urgency` (0.25).
2. Why are safe signals never allowed to soften a message that asks for an OTP?
3. Why did we look at validation errors, not test errors, before changing the rules?

---

## 10. Links

We **never** open links (`urls.py`). Opening a scam link can trigger downloads or tell the scammer your number is active. We only read the link's text.

- **Registered domain**: the part someone actually bought. `secure.sbi.co.in` → `sbi.co.in`; `sbi.kyc-update.xyz` → `kyc-update.xyz` (not SBI!).
- **Look-alike brand**: link mentions "sbi", "hdfc", "paytm"... but the registered domain isn't in the brand's official list → **high risk**. `.gov.in`, `.nic.in` and `.bank.in` count as official because only government bodies and banks can register them.
- **Shorteners** (bit.ly, cutt.ly...) hide the destination → medium.
- **Risky endings** (.xyz, .top, .online...) → medium. **Random digits** in domain → medium.
- **IP address** instead of a name, **punycode** (`xn--`, look-alike Unicode letters), **@ trick**, **.apk** download → high.
- **Defanging**: `https://evil.com` is shown as `hxxps://evil[.]com` so nobody taps it by accident.
- **Google Safe Browsing (optional)**: if you set `GOOGLE_SAFE_BROWSING_API_KEY`, the link (only the link, never the message) is checked against Google's list of dangerous sites. Free for non-commercial use (see `DEPLOYMENT.md`). **Not yet tested with a real key.**

---

## 11. Combining model + rules

```python
risk = max(model_probability, rule_score)
```

`max` means **either** detector can raise the alarm. That favours recall (catch more scams). The cost is a few more false alarms. Evidence it helps: on the challenge set, the model alone caught **28/38** scams; with rules, **33/38**, and false alarms stayed at **0**.

Alternatives you could try (good "future work"): a weighted average, or a small second model that takes both scores as input ("stacking").

---

## 12. Transformers

### 12.1 Embeddings (MiniLM)
A **sentence embedding** model turns a whole message into 384 numbers that capture its *meaning*, so "send me the code" and "share your OTP" end up close together even with no words in common. `paraphrase-multilingual-MiniLM-L12-v2` was pre-trained on 50+ languages. We keep it **frozen** (no retraining) and train a logistic regression on top. About 7–10 ms per message on CPU, but the model is 471 MB.

### 12.2 Fine-tuning MuRIL
**MuRIL** (Google) is a BERT model pre-trained on 17 Indian languages *including transliterated text* (Hindi written in English letters), which is exactly what Hinglish scams are. **Fine-tuning** means continuing to train *all* of its 237 million weights on our labelled messages for a couple of passes (epochs), with a small learning rate (3e-5) so it adjusts rather than forgets. On a laptop CPU this is slow (about an hour here); on a free Colab T4 GPU, a few minutes.

### 12.3 Why compare?
To show the fancy model is worth its cost, or isn't. Results (test set, `reports/RESULTS.md`):

| Model | Recall | False alarms (FPR) | Challenge false alarms | Speed | Size |
|---|---|---|---|---|---|
| **TF-IDF + LogReg + rules (deployed)** | 96.6% | **3.8%** | **0 / 32** | **~2–3 ms** | **1 MB** |
| MiniLM embeddings + LogReg | **97.3%** | 9.6% | 6 / 32 | ~7–10 ms | 471 MB |
| MuRIL fine-tuned (37 min on CPU)* | **97.3%** | 6.1% | 5 / 32 | ~30 ms | 950 MB |

*MuRIL was not re-run after the 25 Nov 2026 split fix (about 3 hours on a 4-core CPU; minutes on a Colab GPU), so its numbers come from the earlier split, in which CloveAI templates leaked into training, and are not directly comparable.

The transformers catch a few more test scams but raise far more false alarms, and are much slower and hundreds of times bigger. Notice its flag threshold was only **0.03**: fine-tuned transformers are often *over-confident* (probabilities pushed to 0 or 1), so a fair comparison must tune each model's threshold separately, as `evaluate.py` does. **With small, synthetic data, the simple model + rules is the better engineering choice today.** Re-run the comparison (on a Colab GPU, with a few learning rates/epochs) once you have real data.

---

## 13. Results

All numbers: `reports/RESULTS.md` (re-generate with `python -m training.evaluate`).

**Headline (deployed system, test set of 1,161):** recall **96.6%**, precision **89.6%**, false-alarm rate **3.8%**, missed-scam rate **3.4%**, about **2–3 ms** per message, **1 MB** model.

**Challenge set (70 hand-written cases):** caught **33/38 scams**, **0/32 false alarms**; **all 14** scary-looking genuine messages correctly left green; but only **4/9 disguised scams** caught. The misses: "O.T.P" with dots, "the code that came on your phone", the CVV described without the word (English and Hindi), and a friendly-sounding job scam.

**Fairness by language (test):** false-alarm rate English **1.0%**, Hinglish **20%**, Hindi **33%** (only 12 genuine Hindi messages: 4 false alarms). **This is the biggest weakness.** Hindi-speaking seniors, the very users the project is for, would see more false 🟡 warnings. Crucially, **every model shows the same gap**, even MuRIL, which was built for Indian languages (Hindi 50%, Hinglish 30%, measured on the earlier split). So it isn't a "wrong model" problem; it's a **data** problem: too few genuine Hindi/Hinglish examples, and a different scam/safe balance per language. A bigger model can't fix missing data.

**Scam type shown:** right for **56/113** caught synthetic scams and **26/33** challenge scams. Most errors are "Type unclear", not wrong types.

**Research experiment (does Indian data matter?)**, same model, more data:

| Trained on | Catches Indian-style synthetic scams | Challenge-set AP |
|---|---|---|
| UCI only (English, UK/SG) | **27%** | 0.64 |
| + CloveAI (templated Indian) | 32% | 0.78 |
| + synthetic Indian (multilingual) | **95%** | **0.99** |

**Conclusion you can defend:** an English-only spam model is nearly useless on Indian scams, and templated data barely helps. Diverse, realistic Indian examples are what make it work. That's the scientific case for collecting real community data next.

### Quiz 13
1. What is the false-alarm rate for Hindi, and why should you be careful about the exact number?
2. Which result best supports "we need real Indian data"?
3. Name two kinds of disguised scams the system misses.

---

## 14. OCR

Many people receive scams as images or want to send a screenshot. **OCR (optical character recognition)** turns an image into text. We use **Tesseract** (free, open source) with English + Hindi language packs (`eng+hin`). `ocr.py` converts to greyscale and enlarges small screenshots before reading. Protections: max 6 MB, a pixel limit against "decompression bomb" images, and the image is never saved. **Status: experimental.** Tested on one generated English image; real phone screenshots in Hindi still need testing.

---

## 15. The website and API

- **HTTP API**: the website (JavaScript in the browser) sends the message to the server as **JSON** (`POST /api/check {"text": "...", "lang": "hi"}`) and gets the result back as JSON. The bot uses the same Python function directly.
- **FastAPI** checks the input (`pydantic`: text must be 1–10,000 characters) and auto-generates API docs at `/api/docs`.
- **Rate limit**: 30 checks per minute per IP, so nobody can flood the server. IPs stay in memory for 60 seconds only.
- **Security headers**: `Content-Security-Policy` allows only our own scripts and styles (blocks injected scripts); `X-Frame-Options: DENY` (no hiding our page inside another site).
- **XSS protection**: the website inserts server text with `textContent`, never `innerHTML`, so a scam message containing `<script>` is shown as text, not run.
- **Private dashboard**: `/api/stats?public=0` needs the `ADMIN_TOKEN` header, compared with `hmac.compare_digest`, which is safe against timing tricks.

---

## 16. The bot

- **Long polling**: the bot asks Telegram "anything new?" every few seconds (`getUpdates`), so no public server is needed.
- **Inline buttons**: "Why?", "What should I do?", "👍 Helpful", "Was this wrong?", language switch.
- To make the language button work **without keeping the message**, the bot computes the result in both languages straight away and keeps only those *results* for 30 minutes.
- `BotLogic` (decisions) is separate from `TelegramApi` (network). That's why it can be tested with a fake Telegram.
- Voice notes: not supported; the bot politely asks for the text instead.

---

## 17. Privacy and security by design

| Risk | What we do |
|---|---|
| Storing people's private messages | Never stored or logged; processed in memory |
| Identifying users from stats | Only daily counts by verdict/type/language/channel; public view hides any group < 5 |
| Counting weekly bot users | Keyed hash (HMAC-SHA256) of the chat id with a secret that **changes weekly and old secrets are deleted**, so it can't be reversed or linked across weeks |
| Sending data to Google | Only links, only if you enable Safe Browsing; disclosed in the privacy policy |
| Leaked API keys | Keys only in environment variables / `.env` (git-ignored); `.env.example` has no real values |
| Malicious model files | `joblib.load` can run hidden code, so only load models you trained |
| Real research data in a public repo | `data/collected/` is git-ignored; anonymise before saving (`text_utils.anonymise`) |
| Over-trust | Every reply says it can be wrong; green never says "safe"; always points to 1930 / cybercrime.gov.in |

The test `test_stats_db_never_contains_message_text` **proves** that after checks via website and bot, the database contains neither the message text nor the chat id.

---

## 18. Designing for elderly users

- Verdict = **emoji + WORD + colour**, never colour alone (about 1 in 12 men are colour-blind).
- Replies ≤ 5 lines; top 2 reasons only; "Why?" button for more.
- Plain words: "It asks for your OTP. No real bank ever asks for this." Not "credential-harvesting attempt".
- Language: we can't know the user's language from the scam (the scammer wrote it), so we guess (Hindi for Hindi/Hinglish messages) and offer a one-tap switch.
- Website: base font 20 px, big buttons (≥ 48 px), high contrast, works on small phones and slow internet, no external fonts or libraries.
- **None of this has been tested with real elderly users yet.** That's Phase 4 in `TIMELINE.md`, with the success criterion "5 users check a message alone in under 1 minute".

---

## 19. Testing

`python -m pytest` runs 36 tests:
- `test_text_and_urls.py`: language detection, link finding, defanging, anonymisation, look-alike domains.
- `test_rules_and_detector.py`: OTP requests in 3 languages, negation ("do not share"), safe signals, verdicts, Hindi replies, 1930 always present.
- `test_api_bot_stats.py`: API, rate limit, admin token, screenshot OCR, upload size and pixel limits (screenshots kept in memory, never spooled to disk), the whole bot conversation, and the privacy test.

A test once failed only sometimes ("flaky"): it checked that a random hex hash didn't contain "42", which happens by chance about 6% of the time. The fix was to test the right thing (the raw id `tg:42` is not stored). Lesson: a flaky test is a bug in the test.

---

## 20. Limitations

Say these yourself, before a judge does:
1. **No real Indian user data.** All results are on public/synthetic data; real-world accuracy is unknown.
2. **Small Hindi/Hinglish test sets** (26 and 94) → wide uncertainty (Hindi false-alarm rate 33%, 95% CI 8–64%; see `reports/BOOTSTRAP_CI.md`).
3. **Higher false alarms for Hindi/Hinglish** (20–33% vs 1% English): a fairness problem.
4. **Disguised scams**: only 4/9 caught.
5. **Scam type** often "unclear".
6. **Synthetic data** was written by AI models; real scammers may write differently.
7. **UCI "spam"** includes marketing, so the label definition is mixed.
8. **OCR and Safe Browsing** are barely tested; **voice** is not implemented.
9. **Not tested with real users**; no workshops yet.
10. **Rules were tuned by one person** after looking at validation errors, so they carry that person's assumptions.

---

## 21. Interview questions with answers

**Q: Why didn't you just use ChatGPT/an LLM?** A: Cost (free tools only), privacy (sending people's private messages to a third party), speed (2 ms vs seconds), and explainability. An LLM comparison is good future work.

**Q: Your recall is 96.6%. Is that good?** A: On this test set, yes. But it's public and synthetic data, so the real-world number is unknown. That's why the next step is collecting real, consented messages.

**Q: What was the hardest bug?** A: Data leakage from templated data. Random splitting would have given near-perfect fake scores. I grouped messages by template so no template is in both training and test. Then a second, sneakier version of it: because pandas 3 changed how `groupby().apply()` works, the step that capped CloveAI templates silently dropped the template column, so the leakage check had nothing to check and CloveAI templates crossed splits again (CloveAI test scores were a fake-perfect 1.000). A test now fails if any row has no group.

**Q: Why a yellow "suspicious" level?** A: Honesty about uncertainty. A binary yes/no forces the system to pretend it's sure.

**Q: What's your biggest weakness?** A: False alarms on Hindi messages are much higher than on English. I found it by measuring per language, fixed part of it with error analysis on validation data, and the rest needs real Hindi data.

**Q: How do you protect privacy?** A: Messages are never stored; only anonymous counts; weekly-rotating hashed user counts; public stats hide small groups; and a test proves the database never contains message text.

**Q: Why is the threshold not 0.5?** A: Because a missed scam costs far more than a false alarm. I picked the threshold on validation data to catch ≥ 97% of scams.

**Q: Why character n-grams?** A: Hinglish has no standard spelling ("jayega"/"jaega"), and scammers misspell on purpose ("acc0unt"). Letter-chunks still match.

**Q: Did you check what the model learned?** A: Yes. It partly relied on shortcuts like "http" vs "https" from templated data and British words from UCI. That's a dataset problem, and a reason for real data.

**Q: How would you keep it up to date as scams change?** A: The "Was this wrong?" button counts reported misses; with consent, collect new examples monthly, label, re-train, and re-run the same evaluation before deploying.

**Q: What part did you do yourself?** A: *Answer this truthfully, for example:* "The first version was AI-assisted. I then [rebuilt the baseline myself / collected and labelled N real messages / ran the usability test / fixed X]." Only claim what you actually did.

---

## 22. Glossary

| Term | Meaning |
|---|---|
| Adversarial example | A message written to fool the detector |
| AP (average precision) | Area under the precision-recall curve |
| Class imbalance | Far fewer scams than safe messages |
| Confusion matrix | The 2×2 table of TP/FP/FN/TN |
| Data leakage | Test information sneaking into training, giving fake-good scores |
| Defang | Make a link unclickable (`hxxp`, `[.]`) |
| Embedding | A list of numbers representing meaning |
| Epoch | One pass over all training data |
| F1 | Harmonic mean of precision and recall |
| Fine-tuning | Further training of a pre-trained model on your task |
| FNR / FPR | Missed-scam rate / false-alarm rate |
| Hard negative | A genuine message that looks like a scam |
| HMAC | A keyed hash; can't be reversed or recomputed without the key |
| n-gram | A sequence of n words (or n letters) |
| Noisy-OR | 1 − Π(1 − wᵢ): combines independent signals |
| OCR | Reading text from images |
| Precision / Recall | Share of flags that are right / share of scams caught |
| Regularisation (C) | Penalty that keeps weights small to avoid memorising |
| Stratified split | Split that keeps the class ratio the same |
| Template | Messages identical except for numbers/names |
| Threshold | The probability above which we flag |
| TF-IDF | Term frequency × inverse document frequency |
| Transliteration | Writing one language in another's script (Hindi in English letters) |

---

## 23. Quiz answers

**Quiz 1:** (1) Normalise + language → links → rules → model → combine → thresholds → reply. Step 7 (`messages.py` strings) produces the words. (2) Rules explain and catch known tricks with little data; the model generalises from examples; each covers the other's gaps. (3) A model can be wrong; "safe" would create false trust that a scammer could exploit.

**Quiz 4:** (1) Copies of the same template end up in both train and test, so the model has seen the "answers". (2) Validation. Using test would make the final score an over-optimistic, tuned number. (3) A shop's sale promotion.

**Quiz 6:** (1) Squashes any score into 0..1 so it can be read as a probability. (2) Overfitting: memorising training quirks, worse on new messages. (3) It's a shortcut from how templated data was generated, not a real scam signal; real scammers use https too.

**Quiz 7:** (1) 284 / (284 + 100) = 0.74. (2) Recall (or FNR) for "few missed"; precision or FPR for "rarely cry wolf". (3) With ~75% safe messages, "always safe" is ~75% accurate but catches nothing.

**Quiz 8:** (1) Yellow's job is to catch nearly every scam (recall); red's job is to be trustworthy when it shouts (precision). (2) Many more false alarms; people would learn to ignore warnings. (3) Otherwise the test score is no longer an honest estimate.

**Quiz 9:** (1) 1 − (0.35 × 0.75) = 0.7375 → 🔴. (2) Scammers can copy polite phrases; an OTP request is dangerous no matter how polite. (3) So the test set stays an unbiased final exam.

**Quiz 13:** (1) 33%, but it's 4 errors out of only 12 genuine Hindi messages, so the real rate could be much higher or lower. (2) The cross-dataset experiment: 27% → 95% recall on Indian-style scams when Indian data is added. (3) Any two of: "O.T.P" with dots; "the code that came on your phone"; CVV described as "3 digits on the back"; friendly job-offer opener.
