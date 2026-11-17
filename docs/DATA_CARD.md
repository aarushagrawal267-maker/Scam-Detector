# Data card

*Last updated 2026-11-17. Re-create all processed data with `python -m training.prepare_data`.*

## The most important fact

**There are no real messages from Indian users in this dataset yet.** Everything below is public data that is either real but foreign and old (UCI), or Indian-style but machine-generated (CloveAI, synthetic). Any accuracy number from this data tells you how the model behaves on *this* data. It does **not** tell you how well it protects an elderly person in India. Collecting real, consented, anonymised messages (see `LABELING_GUIDE.md`) is the most important next step of the project.

## Sources used

| Source | What it is | Rows used | Label meaning | Language | Licence | Known problems |
|---|---|---|---|---|---|---|
| [UCI SMS Spam Collection](https://huggingface.co/datasets/ucirvine/sms_spam) (Almeida, Gómez Hidalgo & Yamakami, 2011) | Real SMS from the UK and Singapore, about 2011 | 5,105 after removing duplicates | `spam` includes ordinary marketing, not only scams | English | The HF card says "unknown"; the UCI repository lists CC BY 4.0. Verify before publishing. | Old and foreign; "spam" ≠ "scam"; UK words ("txt", "claim", "£") become shortcuts |
| [CloveAI/india-spam-sms](https://huggingface.co/datasets/CloveAI/india-spam-sms) | Indian-style SMS (banks, telecoms, couriers), 20,010 rows | 1,378 (capped) | spam/scam vs. normal | English (Indian context) | MIT | **Built from only ~121 templates** with numbers and names swapped; no documentation of how it was made; slot-filling errors ("recharge of INR 2GB/day") |
| [Ridham115/indian-scam-sms-synthetic-audited](https://huggingface.co/datasets/Ridham115/indian-scam-sms-synthetic-audited) | 1,580 messages written by LLMs (Gemini, gpt-oss) and partly audited by people | 1,580 | scam vs. genuine look-alike | English, Hindi, Hinglish, Bengali/Marathi/Tamil/Telugu + English | CC BY 4.0 | Synthetic: its own card says *do not use to estimate real-world accuracy*; 1,350 rows unreviewed |

### Sources looked at and rejected

| Source | Why rejected |
|---|---|
| karanverma19/Indian_Multilingual_Scam_Message_Dataset | 120 rows, of which 71 are duplicates; labels look template-generated and inconsistent ("Thank you for your purchase jaldi kare" = legit) |
| dbarbedillo/SMS_Spam_Multilingual_Collection_Dataset | Machine translation of UCI; the Hindi translations are often garbled. Training on them would also leak UCI test messages into training (same message, different language). GPL licence |
| gandharvbakshi/SMS-dataset-OTP-OTP_INTENT_Phishing | Gated (access request needed); not used |

## Processing steps (`training/prepare_data.py`)

1. **Normalise** text (Unicode NFKC, remove zero-width characters, collapse spaces).
2. **Exact duplicates removed:** 1,194.
3. **Template grouping:** numbers → `0`, links → `URL`, Capitalised words → `W`. Messages with the same key form one group.
4. **CloveAI capped** at 15 messages per template (19,230 → 1,378) so 121 templates don't dominate.
5. **Grouped, stratified split** per source: 70% train / 15% validation / 15% test. A group never crosses splits; an automatic check enforces this.

## Final splits

| Split | UCI safe / spam | CloveAI safe / scam | Synthetic safe / scam | Total |
|---|---|---|---|---|
| train | 3,227 / 458 | 544 / 440 | 559 / 569 | 5,797 |
| val | 645 / 92 | 109 / 88 | 112 / 114 | 1,160 |
| test | 646 / 92 | 109 / 88 | 112 / 114 | 1,161 |

Language mix of the test set: English 970, Hinglish 94, Hindi 26, Bengali-English 23, Marathi-English 22, Telugu-English 14, Tamil-English 12. **Hindi and Hinglish test sets are small**, so their scores have wide error bars (e.g., 26 Hindi messages: one mistake moves recall by about 7 points).

## Challenge set (`data/challenge/challenge_set.csv`)

70 short test cases **hand-written for this project** (38 scams, 32 genuine): 49 English, 11 Hinglish, 10 Hindi. They include 9 *adversarial* scams (disguised spelling, "code" instead of "OTP", the CVV described without the word) and 14 *hard negatives* (genuine messages that look scary: real OTP messages, real KYC reminders that send you to a branch, real power-cut notices). They are not real messages. They are **never used for training** and work like an exam the model has never seen. All phone numbers and links in them are fake.

## Real data you will collect (planned, not started)

Follow `LABELING_GUIDE.md`. Store collected messages in `data/collected/` (ignored by git). **Never commit real messages to this public repository.** Record for each: source (e.g., "family WhatsApp, with consent"), date, language, label, category, and who labelled it.
