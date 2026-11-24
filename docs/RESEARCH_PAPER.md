# Detecting Scam Messages for Multilingual Indian Users: Templated Data Inflates Scores, Diverse Data Generalises

*Draft v0.1, 17 Nov 2026. Author: [student name], [school], [city], India. AI-assistance statement: the first implementation and this draft were produced with an AI coding assistant; [describe your own contributions here]. Sections marked **[FUTURE]** describe work not yet done and must not be presented as results.*

## Abstract
Older adults in India are frequent targets of SMS and WhatsApp scams written in English, Hindi and code-mixed Hinglish. Public spam datasets are mostly English, old and foreign. We build an explainable detector that combines a TF-IDF + logistic-regression classifier with 22 multilingual red-flag rules and offline link analysis, and outputs a three-level verdict (SCAM / SUSPICIOUS / LIKELY SAFE) with plain-language reasons. Using leakage-free, template-grouped splits of three public datasets (one real English, one template-generated Indian, one LLM-generated multilingual Indian), the deployed system reaches 96.6% recall and 90.2% precision (false-positive rate 3.6%) on 1,161 held-out messages, at about 2 ms per message. On 70 hand-written challenge cases it catches 33/38 scams with no false alarms, but only 4/9 deliberately disguised scams. A cross-dataset experiment shows that a model trained only on English UK/Singapore SMS catches 27% of Indian-style scams, versus 95% after adding diverse Indian examples. Templated Indian data yields a perfect in-distribution score but little transfer. False-positive rates are markedly higher for Hindi (25%) and Hinglish (20%) than English (0.9%), and this gap persists for every model tested, including a fine-tuned Indian-language transformer (MuRIL), which did not outperform the simple model overall. These results are on public and synthetic data only; real-world performance remains to be measured.

## 1. Introduction
[Problem: scale of scam messages in India, with *verified* statistics and citations from official sources (I4C / NCRB / RBI annual reports). **Do not add numbers you have not verified.**]
Most anti-spam tools are English-first and do not explain their decisions. Older users with limited tech confidence need (a) their language, (b) a clear verdict that never over-promises safety, and (c) a concrete next step.

**Research questions**
- RQ1: How well does a lightweight, explainable model detect scam messages across English, Hindi and Hinglish?
- RQ2: Does adding Indian-style training data improve detection of Indian-style scams, and does the *kind* of data (templated vs. diverse) matter?
- RQ3: Do hand-written red-flag rules add value on top of the statistical model?
- RQ4 **[FUTURE]**: Can older adults use the tool independently, and do explanations improve their scam awareness?

**Hypotheses.** H1: Training on English-only data transfers poorly to Indian-style scams. H2: Diverse multilingual examples help more than templated ones. H3: Rules increase recall on unseen tricky cases without raising false alarms.

## 2. Background and related work
- SMS spam detection with classical models on the UCI SMS Spam Collection (Almeida, Gómez Hidalgo & Yamakami, 2011).
- Multilingual transformers: BERT (Devlin et al., 2019); MuRIL for Indian languages including transliterated text (Khanuja et al., 2021); multilingual sentence embeddings via knowledge distillation (Reimers & Gurevych, 2020).
- [Add after a literature search: prior work on Indian / code-mixed SMS spam and phishing, explainable spam detection, and technology use by older adults. Cite only papers you have read.]

## 3. Data
See `DATA_CARD.md`. Three sources: UCI (real, English, 5,105 after de-duplication), CloveAI india-spam-sms (20,010 rows from ~121 templates, capped to 1,378), and Ridham115 synthetic audited (1,580 LLM-written, multilingual, with genuine look-alike "hard negatives").
**Leakage control:** messages were grouped by a template key (digits, links and capitalised words masked), and whole groups were assigned to one split (70/15/15, stratified by label, per source). An assertion verifies that no group crosses splits.
**Challenge set:** 70 hand-written cases (38 scams incl. 9 adversarial; 32 genuine incl. 14 hard negatives) in English, Hindi and Hinglish. Never used for training or tuning.
**Ethics:** only public datasets and author-written examples; no personal data collected. **[FUTURE]** real messages will be collected only with consent and anonymised (see `LABELING_GUIDE.md`, `PILOT_PROTOCOL.md`).

## 4. Methods
**Baseline:** TF-IDF on word 1–2-grams and character 2–5-grams (within word boundaries) → logistic regression with balanced class weights; C ∈ {0.3, 1, 3, 10, 30} selected by validation average precision (C = 10).
**Rules:** 22 regular-expression rules in English, Hinglish and Devanagari Hindi (e.g., OTP requests with negation handling, UPI-PIN-to-receive, authority threats / "digital arrest", look-alike links), combined by noisy-OR, plus "safe signals" that halve the rule score unless a high-danger rule fires. After one round of **validation-set** error analysis, the KYC rule weight was reduced (0.45 → 0.25) and safe signals were added.
**Link analysis:** offline features only (look-alike brand domains, shorteners, high-risk TLDs, digits/hyphens, IP hosts, punycode, `.apk`); links are never opened.
**Hybrid:** risk = max(model probability, rule score). Two thresholds from validation: SUSPICIOUS (recall ≥ 0.97) and SCAM (precision ≥ 0.97).
**Comparison models:** (a) frozen multilingual MiniLM sentence embeddings + logistic regression; (b) MuRIL-base fine-tuned for 2 epochs (CPU, lr 3e-5, max length 128, class-weighted loss). Each system's flag threshold was tuned on validation with the same rule.
**Metrics:** precision, recall, F1, FPR, FNR, AP, ROC-AUC; breakdowns by source, language and scam type; type-label accuracy; latency.

## 5. Results
(All numbers from `reports/RESULTS.md`, generated by `training/evaluate.py`.)

**5.1 Overall (test, n = 1,161, 294 scams)**

| System | Precision | Recall | FPR | AP |
|---|---|---|---|---|
| Rules only | 0.841 | 0.721 | 0.046 | 0.746 |
| TF-IDF + LogReg | 0.916 | 0.969 | 0.030 | 0.989 |
| **TF-IDF + LogReg + rules (deployed)** | **0.902** | **0.966** | **0.036** | **0.988** |
| MiniLM embeddings + LogReg | 0.826 | 0.969 | 0.069 | 0.968 |
| MuRIL fine-tuned (2 epochs, CPU) | 0.844 | 0.973 | 0.061 | 0.986 |

MuRIL reached the highest test recall but nearly doubled the false-positive rate, raised 5/32 false alarms on the challenge set (deployed: 0), and was ~15× slower (30.5 vs ~2 ms per message) and ~950× larger.

**5.2 Challenge set (n = 70).** Model alone: 29/38 scams, 0 false alarms. Deployed hybrid: 33/38 scams, 0/32 false alarms; 14/14 hard negatives correct; 4/9 adversarial scams caught. Misses: punctuated "O.T.P", "the code that came on your phone", CVV described without the word (English and Hindi), and a friendly job-scam opener. **This supports H3.**

**5.3 Cross-dataset experiment (RQ2).** Same model trained on growing data, threshold 0.5:

| Trained on | Recall on synthetic Indian test | AP on challenge set |
|---|---|---|
| UCI only | 0.272 | 0.637 |
| UCI + CloveAI | 0.412 | 0.793 |
| UCI + CloveAI + synthetic | 0.947 | 0.983 |

Training with CloveAI gives AP = 1.000 on CloveAI's own test split, but challenge-set recall of only 0.263, so **templated data inflates in-distribution scores without transferring**. **This supports H1 and H2.**

**5.4 Fairness across languages.** Deployed system false-positive rate: English 0.009, Hinglish 0.20, Hindi 0.25 (12 genuine Hindi messages), other code-mixed varieties 0.08–0.50 (n ≤ 13 genuine each). Recall was ≥ 0.92 in all languages. **The gap appears in every system tested** (`reports/RESULTS.md`, "False alarms by language"), including MuRIL, which was pre-trained on Indian languages (Hindi FPR 0.50, Hinglish 0.30). The disparity is therefore likely driven by the training data (few genuine non-English examples, with different label balance per language) rather than by model choice.

**5.5 Scam type.** Correct type for 56/112 caught synthetic scams and 26/33 caught challenge scams; most errors were "type unclear" rather than a wrong type.

**5.6 Cost.** Deployed system: ~2 ms per message on a laptop CPU, 1 MB. MiniLM: ~7 ms, 471 MB.

## 6. Discussion
- The simple, explainable model was competitive with larger multilingual models on this data (MuRIL: AP 0.986 vs 0.989, but more false alarms), so model size is not the bottleneck; **data is**. MuRIL was trained on CPU for only 2 epochs without hyper-parameter search; a GPU run with tuning may do better and is part of future work.
- Feature inspection revealed shortcuts (`http` vs `https`, British SMS words, a Devanagari character), consistent with the language-dependent false-positive rates.
- Rules contributed recall on unseen phrasing and supplied the plain-language explanations users see.

## 7. Limitations
No real Indian user messages; small Hindi/Hinglish test sets with wide bootstrap 95% confidence intervals (false-alarm rate: Hinglish 0.20, CI 0.09–0.32; Hindi 0.25, CI 0.00–0.53; English 0.009, CI 0.003–0.016; see `reports/BOOTSTRAP_CI.md`); synthetic data written by LLMs; UCI "spam" includes marketing; rules written and revised by one person; no user study yet; OCR barely tested; voice not implemented.

## 8. Future work **[FUTURE]**
1. Collect ≥ 300 consented, anonymised real messages; double-label; report Cohen's κ; re-evaluate (the key test of RQ1).
2. Usability study with older adults (RQ4) under ethics approval (`PILOT_PROTOCOL.md`): task success, time, comprehension of the three verdicts, pre/post awareness quiz.
3. Reduce Hindi/Hinglish false positives (more genuine Hindi data, per-language thresholds, debiasing).
4. New adversarial test set; text normalisation for disguised spellings; learned scam-type classifier.
5. Fine-tune MuRIL on a GPU with real data; compare with an LLM-based classifier on cost, privacy and accuracy.

## References
- Almeida, T. A., Gómez Hidalgo, J. M., & Yamakami, A. (2011). Contributions to the study of SMS spam filtering: New collection and results. *Proceedings of the 11th ACM Symposium on Document Engineering (DocEng '11)*.
- Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. *NAACL-HLT 2019*.
- Khanuja, S., et al. (2021). MuRIL: Multilingual Representations for Indian Languages. *arXiv:2103.10730*.
- Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830.
- Reimers, N., & Gurevych, I. (2020). Making monolingual sentence embeddings multilingual using knowledge distillation. *EMNLP 2020*.
- Smith, R. (2007). An overview of the Tesseract OCR engine. *ICDAR 2007*.
- Datasets: CloveAI/india-spam-sms (Hugging Face, MIT); Ridham115/indian-scam-sms-synthetic-audited (Hugging Face, CC BY 4.0).

*Before submitting anywhere: re-read every reference yourself, and check each journal's rules on AI assistance and human-participant research.*
