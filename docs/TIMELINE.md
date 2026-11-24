# Timeline: what is done, and when everything else gets done

*Written 2026-11-17. Dates after today are **targets** for you, assuming about 8 hours a week. Move them if your school calendar or application deadline needs it.*

---

## Part A: Completed on 17 November 2026 (built with AI assistance in one session)

Everything in this table exists in the repository and was tested in this session. "Tested" means automated tests or the evaluation script ran. **None of it has been used by a real elderly person yet.**

| # | Item | Status | Where | How it was checked |
|---|---|---|---|---|
| 1 | Project structure, requirements, `.gitignore`, `.env.example` | ✅ Done | repo root | – |
| 2 | Data pipeline: download 3 public datasets, clean, de-duplicate, template grouping, leak-free 70/15/15 split | ✅ Done | `training/prepare_data.py` | Built-in check that no template crosses splits |
| 3 | Hand-written challenge set (70 tricky cases, 3 languages) | ✅ Done | `data/challenge/challenge_set.csv` | – |
| 4 | Baseline model: TF-IDF (words + characters) + logistic regression | ✅ Done | `training/train_baseline.py`, `models/baseline.joblib` | Validation-tuned C and thresholds |
| 5 | Advanced model A: multilingual MiniLM embeddings + logistic regression | ✅ Done (comparison only, not deployed) | `training/train_transformer.py --mode embed` | `reports/RESULTS.md` |
| 6 | Advanced model B: MuRIL fine-tuned (CPU, 2 epochs, 37 min) | ✅ Done (comparison only, not deployed; weights not kept, 950 MB) | `training/train_transformer.py --mode finetune` | `reports/RESULTS.md` |
| 7 | Red-flag rules in English, Hinglish and Hindi (22 rules + "safe signals") | ✅ Done | `scam_detector/rules.py` | Unit tests + validation error analysis |
| 8 | Link checker (look-alike brands, shorteners, risky endings, .apk, IP, punycode) + optional Google Safe Browsing | ✅ Offline checks done. Safe Browsing ⚠️ written but **never tested with a real key** | `scam_detector/urls.py` | Unit tests |
| 9 | Hybrid verdict 🔴/🟡/🟢, scam type, plain-language reasons, advice, in English + Hindi | ✅ Done | `scam_detector/detector.py`, `messages.py` | Unit tests |
| 10 | Full evaluation: per model, per source, per language, per scam type, challenge set, speed, cross-dataset experiment | ✅ Done | `training/evaluate.py` → `reports/RESULTS.md` | – |
| 11 | Web API (check text, check screenshot, feedback, stats) with rate limiting and security headers | ✅ Done | `app/server.py` | API tests |
| 12 | Website: check box, screenshot upload, common scams, guide, privacy page, public stats | ✅ Done | `app/static/` | Browser tests at phone and desktop width |
| 13 | Printable 2-page workshop guide (English + Hindi) | ✅ Done | `docs/printable-guide.pdf` | – |
| 14 | Telegram bot (text, screenshots, buttons, language switch, feedback) | ⚠️ Code done, tested with a fake Telegram. **Never run on real Telegram** (needs your bot token) | `bot/telegram_bot.py` | Bot tests |
| 15 | Screenshot reading (OCR, English + Hindi) | ⚠️ Experimental: tested on one generated English image only | `scam_detector/ocr.py` | 1 test |
| 16 | Anonymous statistics + private/public dashboard | ✅ Done | `scam_detector/stats.py`, `stats.html` | Test proves message text never reaches the database |
| 17 | 32 automated tests | ✅ All passing | `tests/` | `python -m pytest` |
| 18 | Documents: data card, model card, labelling guide, pilot protocol + consent forms (EN/HI), privacy policy, accessibility checklist, impact tracking, deployment guide, outreach plan, competitions, research paper draft, learning guide | ✅ Drafted | `docs/` | Contacts and competition facts checked on official sites 2026-11-17 (some marked NOT VERIFIED) |
| 19 | Added 24 Nov 2026: MIT licence, Dockerfile (with OCR), README screenshots/API/limitations, upload size + pixel limits (screenshots kept in memory), rate-limiter memory cap, bootstrap 95% confidence intervals | ✅ Done | `Dockerfile`, `app/server.py`, `training/bootstrap_ci.py` → `reports/BOOTSTRAP_CI.md` | 36 tests pass; baseline training + evaluation re-run from scratch reproduced the published numbers |

### Feature status (the honest list)

| Capability | Status |
|---|---|
| SMS / WhatsApp text scam detection | **Fully implemented**, evaluated only on public + synthetic data |
| Phishing-link analysis | **Fully implemented** (offline). Google Safe Browsing: **experimental** |
| Fake bank / KYC, OTP theft, lottery, job offer, delivery fee, electricity bill, loan | **Implemented**, with synthetic test data per type |
| Family impersonation, investment/crypto, romance, fake police / "digital arrest", remote-access apps | **Implemented as rules only**; tested only on a few hand-written cases → **experimental** |
| English | **Implemented** |
| Hindi, Hinglish | **Partially implemented**: works, but small test sets (26 and 94 messages) and higher false-alarm rates |
| Other code-mixed languages (Bengali, Marathi, Tamil, Telugu + English) | **Experimental**: model only, no rules, high false alarms |
| Scam-type label shown to user | **Partially implemented**: right type about half the time on synthetic data; often "type unclear" |
| Screenshot OCR | **Experimental** |
| Voice-note transcription | **Planned, not implemented** (bot politely asks for text) |
| Explanations | **Fully implemented** |
| User feedback | **Fully implemented** |
| Anonymous statistics | **Fully implemented** |
| Website | **Fully implemented**, not deployed |
| Telegram bot | **Implemented**, not deployed, never run live |
| WhatsApp bot | **Not implemented** (deliberate decision, see `DEPLOYMENT.md`) |
| Real-user testing, workshops, partnerships | **Not started** |

---

## Part B: What only YOU can do, and when

These steps need a real person: understanding, consent, ethics approval, relationships. AI can't do them for you and must not pretend to.

### Phase 0: Own the code (weeks 1–3, **by 7 Dec 2026**)
- Read `docs/LEARNING_GUIDE.md` start to finish; answer every quiz without looking.
- Run everything yourself: tests, training, evaluation, website, bot (create your own Telegram bot token).
- **Re-build the baseline from scratch in a Google Colab notebook without copying**: load the data, TF-IDF, logistic regression, confusion matrix. Your numbers should land near the ones in `reports/RESULTS.md`.
- Find an adult sponsor / supervising teacher (needed for IRIS and for ethics approval).
- **Done when:** you can explain every file in the "project map" of the Learning Guide out loud in 10 minutes.

### Phase 1: Your first real improvements (**by 31 Dec 2026**)
- Write 10 NEW disguised-scam test cases first (keep them hidden from yourself while coding), then add rules or normalisation that fix the 5 challenge-set misses ("O.T.P", "code that came on your phone", CVV described without the word). Measure on your new cases, not the old ones.
- Add a category classifier so fewer scams show "type unclear".
- **Done when:** both changes are committed with before/after numbers in `reports/`.

### Phase 2: Real data, with consent (**Jan–Feb 2027**)
- Follow `LABELING_GUIDE.md`: collect ≥ 300 real messages from family/community **with consent**, anonymise, store outside the repo.
- Get a second person to label 100 of them; compute Cohen's kappa.
- Re-train and evaluate on real data. **This is the most important result of the whole project.**
- **Done when:** `reports/RESULTS.md` has a "real messages" section.

### Phase 3: Ethics approval + deployment (**Feb–Mar 2027**)
- Submit `PILOT_PROTOCOL.md` for ethics/IRB review through your school or IRIS process **before** contacting any participant.
- Deploy: the web app plus the Telegram bot on an always-on computer or a free host (see `DEPLOYMENT.md`; note the free-tier limits).
- **Done when:** approval letter received; bot reachable 24/7 for a week.

### Phase 4: Usability test with 5 older adults (**April 2027**)
- Run the protocol. Don't help them. Record time, errors, quotes.
- Redesign based on what you saw; log changes in the design-change table.
- **Done when:** 5 users each check a message alone in under 1 minute (the success criterion), or you have documented why not and what you changed.

### Phase 5: Workshops + first outreach (**May–Jul 2027**)
- Run 2–3 workshops with the printable guide (senior centre, RWA, temple/gurdwara/church group).
- Contact 1–2 researchers from `OUTREACH_PLAN.md` with your real results (templates there; send from your own email, parent/teacher cc'd).
- Re-train MuRIL on a free Colab GPU with your real data.
- **Done when:** workshops logged in `impact_log_template.csv` with real numbers.

### Phase 6: Paper, competitions, bigger outreach (**Aug–Oct 2027**)
- Finish `RESEARCH_PAPER.md` with real-data and pilot results.
- **IRIS National Fair 2027–28**: registration expected around Aug–Oct 2027 (**NOT VERIFIED**; the 2026–27 window closed 13 Oct 2026). Check the official page monthly from June 2027.
- Contact DSCI (Meri Digital Suraksha) and CERT-In awareness with pilot results.
- **Done when:** submissions made (record dates and confirmation e-mails).

### Phase 7: Application write-up (**by Nov 2027**, or earlier if your deadline is earlier)
- Write the 150-character activity description from **real numbers in your impact log** (`IMPACT_TRACKING.md`).
- Prepare to explain one failure honestly (e.g., the Hindi false-alarm problem, or the templated-data trap).

---

## How to update this file
When you finish something, move it to Part A with the date, the evidence (commit, report, photo of attendance sheet), and who did it. If something was AI-assisted, say so. That honesty is what makes the rest believable.
