# Labelling Guide: Scam Message Dataset

This guide explains how to turn messages you collect (with permission) into a clean, labelled,
anonymised dataset that `training/prepare_data.py` can use. Read it fully before you label
anything. Labelling mistakes become model mistakes. Nothing the model does can be better than its labels.

---

## 0. Safety rules (read first, every time)

1. **Never reply to a scammer.** Not even "stop" or "who is this?". A reply tells them your number is active.
2. **Never click, open or "just check" a link.** Not on your phone, not on a laptop. Don't paste it into a
   browser. Judge a link only by reading its text. When you show a link anywhere (slides, docs, chat), write it
   "defanged": `hxxps://sbi-kyc-update[.]xyz` (http becomes hxxp, every `.` in the domain becomes `[.]`).
3. **Never call or WhatsApp a number in a scam message.**
4. **Never open attachments or `.apk` files.**
5. **Never collect OTPs, PINs, passwords, CVVs or full card/account numbers.** If a message you are given
   contains one (for example, a real OTP message), replace it before saving (see Section 5).
6. **Never collect messages from anyone under 18 without written permission from their parent or guardian.**
7. **Ask before you collect.** Tell the person what the message is for (training a scam-detection model), that
   their name and number will be removed, and that they can ask you to delete it later. Write down that they
   agreed (date + who), and keep that note private.
8. **If someone has just lost money, help comes first, data second.** Tell them to call **1930** and report at
   **cybercrime.gov.in** right away, and to call their bank using the number on their card or passbook.
9. **Keep raw messages private.** The raw collection (before anonymisation) never goes into the public GitHub
   repo. Store it in a private folder or a private Google Sheet shared only with your co-labeller.

India's Digital Personal Data Protection Act, 2023 applies to personal data. Collect the minimum you need, get
consent and remove identifiers. Verify the current version of the Act and its rules before a large collection
drive, or ask your adult sponsor to.

---

## 1. The labels

During labelling, each labeller gives every message one of three labels:

| Label | Meaning | Goes into the final CSV? |
|---|---|---|
| `scam` | The message is trying to trick the reader into giving money, OTP/PIN/passwords, personal data, or control of their phone, by lying about who the sender is or what will happen. | Yes, as `scam` |
| `safe` | A genuine message: personal chat, a real transaction/OTP alert, a real bill, real marketing from a real company, a real government notice. Annoying ≠ scam. | Yes, as `safe` |
| `unsure` | You cannot tell from the text alone. | **No.** Must be resolved first (Section 7). If still unresolved, leave it out and record it in your notes. |

**The key question:** *"If the reader did exactly what this message asks, would they be cheated?"*
Yes → `scam`. No → `safe`. Can't tell → `unsure`.

Label **the message text**, not the sender. You usually can't see the sender ID in a forwarded message. If you
do have extra information (for example, "my uncle confirmed he really did change his number"), you may use it,
but write that down in your private notes so you can explain the label later.

---

## 2. Scam categories

Every `scam` row gets exactly one `category`. Every `safe` row gets `category = none`.
These ids match `scam_detector/messages.py` exactly. Do not invent new ones without also updating the code.

| `category` | What it looks like | Typical signs |
|---|---|---|
| `fake_bank_kyc` | Pretends to be a bank/wallet; "KYC expired", "PAN not linked", "account blocked", fake reward points or refunds | Link to a look-alike site, threat of blocking, urgency |
| `otp_theft` | Asks the reader to share an OTP/PIN, or to enter a UPI PIN / scan a QR code to "receive" money | "Share the code you received", "enter PIN to get refund" |
| `lottery_prize` | "You won" a lottery, KBC prize, lucky draw, gift you never entered | Prize + fee to claim |
| `job_offer` | Easy part-time/work-from-home money; "like videos / rate hotels and earn" | Pay-per-task, then a "deposit" to unlock earnings |
| `family_impersonation` | "Hi Mum/Papa, this is my new number…" followed by a money request | New number + urgent money |
| `delivery_fee` | Fake parcel/courier/India Post message; "parcel held, pay small fee / update address" | Small fee, look-alike courier link |
| `investment_crypto` | Guaranteed returns, stock tips groups, crypto, "double your money" | Guarantees, VIP groups, unrealistic % |
| `romance` | Someone met online asks for money or a "customs fee" for a gift | Emotional language + money |
| `government_impersonation` | Fake police/CBI/customs/TRAI/court; "digital arrest", "drugs found in your parcel" | Threat of arrest + secrecy + payment |
| `electricity_bill` | "Your electricity will be cut tonight, call this officer" | Personal mobile number, tonight deadline |
| `loan_offer` | Pre-approved / no-CIBIL instant loan that needs a fee or an app download | Processing fee, unknown app |
| `remote_access` | Asks to install AnyDesk/TeamViewer/screen-share, or an `.apk` file | App install request |
| `phishing_link` | A scam whose main trick is a dangerous link, and none of the above fits | Look-alike or shortened link |
| `unknown` | Clearly a scam, but no category fits | Use rarely; write a note why |

**If more than one category fits**, choose the one that describes the main trick, i.e. what the scammer finally
wants. If it's still a tie, use this priority order (the same order the code uses in `rules.py`):

`government_impersonation` > `otp_theft` > `remote_access` > `family_impersonation` > `fake_bank_kyc` >
`electricity_bill` > `delivery_fee` > `lottery_prize` > `investment_crypto` > `job_offer` > `loan_offer` >
`romance` > `phishing_link` > `unknown`

Example: "CBI officer: drugs found in your parcel, install AnyDesk now" fits both `government_impersonation` and
`remote_access`, so it gets `government_impersonation`.

---

## 3. Worked edge cases

All examples below were written for this guide. They are not real messages. Links are shown defanged.

| # | Message (shortened) | Label | Category | Why |
|---|---|---|---|---|
| 1 | "482913 is your OTP for txn of INR 2,500 at AMAZON. Valid 10 mins. Do not share OTP with anyone. -HDFC Bank" | `safe` | `none` | A real OTP alert. It *mentions* OTP but tells you **not** to share it. (Replace the code before saving; see Section 5.) |
| 2 | "Sir, I sent an OTP to your number by mistake, please tell me the code" | `scam` | `otp_theft` | Asks the reader to share a code. |
| 3 | "Dear Customer, your KYC is due for periodic update. Visit your home branch or update in the official app. Ignore if done." (no link) | `safe` | `none` | Real banks do send reminders like this. It points to the branch/official app, asks for nothing, and has no link. |
| 4 | "Dear Customer your SBI A/c will be blocked today. Update KYC: hxxp://sbi-kyc-update[.]xyz" | `scam` | `fake_bank_kyc` | Look-alike domain + block threat + urgency. |
| 5 | "Big Billion Days! Up to 80% off. Shop at flipkart[.]com" | `safe` | `none` | Promotional **spam is not a scam**. It's a real company and the real domain. (Public datasets like UCI label this kind of message "spam"; we don't.) |
| 6 | "Flipkart Sale! iPhone at ₹999 for first 100 buyers: hxxp://flipkart-sale99[.]shop" | `scam` | `phishing_link` | Same brand, fake domain, impossible price. |
| 7 | "Hi Nani, it's Riya, I changed my number, save this one. See you Sunday!" | `safe` | `none` | New number but **no request** for money, codes or details. (If you know it was a scam attempt, label it so and note why.) |
| 8 | "Hi Mumma this is my new number, phone fell in water. Need ₹15,000 urgently for fees, will explain later" | `scam` | `family_impersonation` | New number + urgent money + avoids a call. |
| 9 | "₹2,000 instalment under [government scheme] credited to your account ending XX12." (no link, no request) | `safe` | `none` | Genuine-style government credit notice that asks for nothing. |
| 10 | "PM scheme new list released! Download app to check your name: hxxp://scheme-list[.]top/check.apk" | `scam` | `remote_access` | Asks to install an `.apk` from a random link. |
| 11 | "Get personal loan up to ₹5L at 10.5% p.a. from [bank name]. T&C apply. Apply in the [bank name] app." | `safe` | `none` | Normal marketing from a regulated lender: no upfront fee, official channel. |
| 12 | "Pre-approved loan ₹5 lakh without CIBIL! Pay ₹999 processing fee to this UPI ID to release" | `scam` | `loan_offer` | Fee before loan, "no CIBIL". |
| 13 | "Dear consumer, your electricity will be disconnected tonight at 9:30 as last month bill not updated. Contact officer 9XXXXXXXXX" | `scam` | `electricity_bill` | Personal mobile number + tonight threat. |
| 14 | "Your electricity bill of ₹1,250 for Oct is generated. Due date 15 Nov. Pay via official app/website." | `safe` | `none` | Real bill format, no threat, official channel. |
| 15 | "India Post: your parcel is held due to incomplete address. Update within 24 hrs: hxxps://indiapost-redeliver[.]top" | `scam` | `delivery_fee` | Real India Post links end in `indiapost.gov.in`; this doesn't. |
| 16 | "This is CBI. Drugs found in a parcel in your Aadhaar name. You are under digital arrest. Don't tell anyone." | `scam` | `government_impersonation` | Police never "arrest" anyone over a call; secrecy is a big flag. |
| 17 | "Part time job! Earn ₹3,000 daily by liking YouTube videos. WhatsApp HR now." | `scam` | `job_offer` | Pay-for-likes is a known task scam. |
| 18 | "Join our VIP stock group. 30% guaranteed monthly returns." | `scam` | `investment_crypto` | Guaranteed returns don't exist. |
| 19 | "SBI never asks for your OTP, PIN or password. Beware of fraud calls." | `safe` | `none` | An **awareness** message. It's full of scam words, which makes it a great hard negative. |
| 20 | "You have received a collect request of ₹5,000. Enter UPI PIN to receive." | `scam` | `otp_theft` | You never need a PIN to *receive* money. |
| 21 | "hxxps://bit[.]ly/3xYz" (a link and nothing else) | `unsure` | n/a | Can't tell from the text alone. Resolve with your co-labeller; if unresolved, leave it out. |
| 22 | "Hi, is this Mr. Sharma? Long time no see!" (wrong-number opener) | `unsure` | n/a | Often the first step of a romance/investment scam, but the text alone is harmless. Label `scam` (`romance` or `investment_crypto`) **only** if you know what followed, and note it. |
| 23 | A family member forwards a scam and adds "is this real??" on top | label the **scam part** | per the scam | Delete the family member's comment, and label only the original message. |
| 24 | "Your 7,850 reward points expire today! Redeem now: hxxp://hdfc-rewards[.]in" | `scam` | `fake_bank_kyc` | Look-alike bank domain; reward-point bait is a bank-impersonation trick. |

**Hard negatives** (rows 1, 3, 5, 9, 11, 14, 19) are the most valuable `safe` examples: genuine messages that look a
bit like scams. Without them, the model learns "mentions a bank = scam", which leads to false alarms on real
bank messages. Collect them on purpose.

---

## 4. Languages, scripts, emojis and links

**`language` column values:**

| Value | When |
|---|---|
| `en` | English |
| `hi` | Hindi in Devanagari script (आपका खाता…) |
| `hinglish` | Hindi written in English letters, often mixed with English ("aapka account band ho jayega") |
| `other` | Any other language or mix (e.g. Marathi, Tamil or Bengali with English). Note which one in your private notes. |

If a message mixes scripts, choose the script that holds most of the words.

**Do NOT "fix" the text.** Keep it exactly as received:
- **Keep spelling mistakes, odd spacing and ALL CAPS.** Scammers' typos are part of the signal.
- **Do not transliterate.** Don't convert Hinglish to Devanagari or the other way round. The model must learn
  the text people actually receive.
- **Keep emojis** (🎉💰⚠️). They are signal too.
- **Keep amounts** (₹25,00,000). Amounts are not personal data and they help detection.
- **Keep brand names** (SBI, Amazon, India Post) and **keep the link's domain**. They are evidence.
- Line breaks inside a message: keep them; the CSV must then quote the text (Google Sheets does this
  automatically when you download as CSV).

**Links in the dataset:** store them as plain text exactly as they appeared, because the model and the link checker
need the real form. Defang them whenever you display them anywhere else (documents, slides, website examples,
chat). Note: `scam_detector/text_utils.anonymise()` defangs links automatically. If you use it, check how
`training/prepare_data.py` treats defanged links, so that training text and real user text look the same.

---

## 5. Anonymisation checklist

Do this on **every** message before it enters the dataset. First run `anonymise()` from
`scam_detector/text_utils.py` (it handles phone numbers, e-mails and long digit strings), **then check every row by
eye**, because a simple rule cannot reliably find names.

| Remove / replace | Replace with | Notes |
|---|---|---|
| People's names (receiver, family, the scammer's fake name) | `[NAME]` | "Dear Ramesh" → "Dear [NAME]" |
| Phone numbers (anyone's, including the scammer's) | `[PHONE]` | Scam numbers often belong to innocent people whose SIMs were misused |
| Account, card, Aadhaar, PAN, UPI IDs, policy and loan numbers | `[NUMBER]` | Includes "a/c ending 1234" → "a/c ending [NUMBER]" |
| OTPs, PINs and verification codes inside real messages | `[NUMBER]` | Never store a real code, even an expired one |
| E-mail addresses | `[EMAIL]` | |
| Home addresses and exact locations | `[ADDRESS]` | City names are usually fine |
| **Keep** | n/a | Brand/sender names, amounts, link domains, dates, emojis, typos |

Final check before saving each row: *"Could anyone work out who received this message from the row alone?"*
If yes, anonymise more.

**Duplicates:** the same scam is often forwarded to many people. Keep **one** copy in the dataset (count how many
times you saw it in your notes). Near-identical copies (e.g. the same text with a different amount) must never be
split between the training set and the test set. If they are, the test score is inflated, because the model
has already "seen the answer". `training/prepare_data.py` is meant to group them before splitting. Check that it
does whenever you change it.

---

## 6. CSV format

The final file uses UTF-8 encoding and exactly these six columns, in this order:

```
text,label,category,language,source,collected_on
```

| Column | Allowed values | Example |
|---|---|---|
| `text` | Anonymised message, exactly as received otherwise | `Dear [NAME] your SBI a/c will be blocked today...` |
| `label` | `scam` or `safe` (no `unsure` in the final file) | `scam` |
| `category` | A category id from Section 2, or `none` for safe rows | `fake_bank_kyc` |
| `language` | `en`, `hi`, `hinglish`, `other` | `hinglish` |
| `source` | Where it came from: `family_collected`, `volunteer_collected`, `workshop_collected`, or `public:<dataset-id>` | `family_collected` |
| `collected_on` | Date you received it, `YYYY-MM-DD` | `2026-12-03` |

Example rows:

```csv
text,label,category,language,source,collected_on
"Dear [NAME] aapka SBI account aaj block ho jayega. KYC update karein: http://sbi-kyc-update.example",scam,fake_bank_kyc,hinglish,family_collected,2026-12-03
"[NUMBER] is your OTP for txn of INR 2,500. Do not share OTP with anyone. -HDFC Bank",safe,none,en,family_collected,2026-12-04
```

(`.example` is a reserved domain that can never be a real website, which is why documentation examples use it.
Your real dataset keeps the link exactly as received.)

**Excel warning:** Excel can damage Devanagari text and long numbers. Use Google Sheets, then
*File → Download → CSV* (it saves UTF-8), or use Excel's "CSV UTF-8" option.

Keep your **working sheet** separate and private. It can have extra columns (`labeller_A`, `labeller_B`,
`final_label`, `notes`, `consent_note`). Export only the six columns above to the dataset file.

---

## 7. Two-person labelling and Cohen's kappa

One person's labels contain that person's blind spots. So:

1. **Two people label every message independently.** Each labeller hides the other's column until both are done.
2. Compare the two columns. For each disagreement, discuss it using this guide and agree on a final label. If you
   still can't agree, ask a third person (your mentor) or mark it `unsure` and leave it out.
3. **Update this guide** whenever a disagreement shows the rules were unclear. That's how the guide gets better.
4. Report the agreement score (Cohen's kappa) in your paper.

### Why not just "percent agreement"?

If 90% of messages are safe and both of you lazily label almost everything `safe`, you will "agree" about 80%+ of
the time just by chance. Cohen's kappa (κ) measures how much better you agree **than chance**.

### Formula

```
κ = (p_o − p_e) / (1 − p_e)
p_o = observed agreement  = fraction of messages where you both gave the same label
p_e = chance agreement    = sum over labels of (A's fraction for that label × B's fraction for that label)
```

### Tiny worked example (10 messages)

|  | B says scam | B says safe | A total |
|---|---|---|---|
| **A says scam** | 4 | 1 | 5 |
| **A says safe** | 1 | 4 | 5 |
| **B total** | 5 | 5 | 10 |

- p_o = (4 + 4) / 10 = **0.80** (agreed on 8 of 10)
- p_e = (5/10 × 5/10) + (5/10 × 5/10) = 0.25 + 0.25 = **0.50**
- κ = (0.80 − 0.50) / (1 − 0.50) = 0.30 / 0.50 = **0.60**

So 80% raw agreement is only κ = 0.60 once chance is removed.

**Rough guide** (Landis & Koch, 1977, a commonly used rule of thumb rather than a law): 0.41–0.60 is "moderate"
and 0.61–0.80 "substantial". Above 0.80 is "almost perfect". If your κ is below about 0.6, your guide is probably
unclear. Fix the guide and re-label before training.

In Python: `from sklearn.metrics import cohen_kappa_score; cohen_kappa_score(labels_A, labels_B)`.
Compute κ on the **first** independent labels, before discussion. Agreement after discussion is always ~100% and
tells you nothing.

---

## 8. How many examples?

- For a first baseline: **a few hundred real, labelled messages** in total, roughly balanced between `scam` and
  `safe` (include plenty of hard negatives).
- To report accuracy **for one category or one language**, you need at least **~30 test examples in that group**.
  With fewer, one mistake swings the score by several percent. Report those groups as "too few to measure" instead
  of quoting a number.
- Track counts as you go: a pivot table of `label × category × language` in your working sheet.
