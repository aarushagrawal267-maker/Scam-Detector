# Impact Tracking: What to Measure, How, and What Never to Claim

Reviewers, judges and interviewers trust a small, honest, well-evidenced number more than a big vague one.
Start logging on day one, because you can't rebuild history honestly later.

**Your two records:**
1. **`impact_log_template.csv`**: copy it to a private sheet. Add one row every time you work on the project,
   run a session, or contact someone. Delete the three `EXAMPLE` rows first.
2. **The app's anonymous counters**: `/api/stats` (public view) and the private view with the admin token
   (see `app/server.py` and `scam_detector/stats.py`). These are counts only. No messages are stored.

Columns in the log: `date` (YYYY-MM-DD), `activity` (what you did), `type` (`build` / `research` / `workshop` /
`outreach` / `user-test`), `hours`, `people_reached` (people actually present or reached, never estimates),
`evidence_link` (commit, file, photo or letter, kept private if it contains names), `notes`.

---

## 1. Metrics to track from day one

| Metric | Exact definition | Where it comes from | Evidence to keep |
|---|---|---|---|
| Hours worked | Hours you personally spent, logged the same day | Impact log | The log itself + Git commit history |
| Labelled messages | Rows in the final dataset, split by `label`, `category`, `language`, `source` | Dataset CSV (count with pandas) | Data card with counts and date |
| Labeller agreement | Cohen's kappa on first independent labels | `LABELING_GUIDE.md`, Section 7 | Script output |
| Model performance | Precision, recall, F1, false-negative rate, **on a named test set**, with model version and date | Training/evaluation scripts | Results file in `reports/` |
| Real-world model performance | Same metrics, **only** on real, consented, held-out messages | Your own collected test set | Results file; size of test set |
| Checks | Number of messages checked through the website/bot | `/api/stats` → `total_checks`, `by_channel` | Monthly screenshot of the stats page (dated) |
| Weekly bot users | Distinct chat users in a week (anonymous hashed count) | `/api/stats` → `weekly_bot_users` | Dated screenshot |
| User-reported accuracy | correct ÷ (correct + wrong) from the feedback buttons, **always with n** | `/api/stats` → `user_reported_accuracy`, `_n` | Dated screenshot |
| Reported misses | Scams users said were missed (false negatives) and what you changed | Feedback + your notes | Change log / commits |
| Usability results | Task completed alone (x of 5), median time, top problems | Observation sheets (`PILOT_PROTOCOL.md`) | Anonymised summary + design-change log |
| Workshops | Number held, date, organisation type, attendees (headcount) | Impact log; sign-in count | Organiser's confirmation e-mail/letter; photos only with consent |
| Quiz change | Pre/post scores, paired by number card | Workshop quizzes | Anonymised score sheet |
| Partners | Organisations that **agreed in writing** to a specific activity | E-mails / letters | Saved e-mail or signed letter |
| Outreach | Messages sent, replies received, outcome | Impact log (`outreach` rows) | Sent mail + reply |
| Volunteers / club | Students trained to run workshops, workshops they ran | Impact log | Training attendance list |

Take a dated screenshot of `/api/stats` on the 1st of every month. Counters can be reset by accident; screenshots
can't.

---

## 2. How to measure honestly

- **Exclude your own testing.** You, your friends and your demo sessions will create hundreds of checks. Either
  run a separate test copy of the app for development, or write down the dates you tested and subtract those
  days. Say which you did.
- **Name the test set every time you quote accuracy.** "Recall 0.94 on held-out synthetic Indian messages" is
  honest; "94% accurate" is not.
- **Give n with every percentage**, and for groups under ~30 write counts instead: "4 of 5 users" rather than "80%".
- **Date every number:** "as of 1 March 2027: 412 checks". Numbers change; undated ones look made up.
- **Keep the raw evidence** (screenshots, sign-in counts, e-mails) in a private folder linked from the log.
- **Record failures too.** Missed scams, confused users and unanswered e-mails make the strongest essays and
  interview answers, because they show you learned something.

---

## 3. What NOT to claim

| Don't say | Why it's wrong | Say instead |
|---|---|---|
| "[N] users" when you mean checks | One person can check 20 messages, and you checked many yourself | "[N] messages checked (excluding my own testing)" |
| "Detected [N] scams" | It's the model's verdict count. Some were false alarms, and you don't know the truth for most | "Flagged [N] messages as likely scams" |
| "Saved ₹[X]" or "protected [N] people" | You can't know whether anyone would have fallen for the scam | "[N] people attended workshops; quiz scores went from [a] to [b]" |
| "[X]% accurate" (from the synthetic or public test set) | Synthetic/public data is easier and different from real messages | "[X]% recall on [named] test set; real-world accuracy not yet measured" |
| Training-set accuracy | The model has seen those exact messages | Only test-set results, on data the model never saw |
| "Accuracy" alone | Hides missed scams when most messages are safe | Precision, recall and **false-negative rate** |
| "Partnered with [organisation]" after a polite reply | A reply is not a partnership | "Ran a workshop at [org] on [date]" (only with written agreement) |
| "Endorsed / approved / certified by CERT-In, I4C, RBI, DSCI…" | Never true unless you have a written endorsement, and these bodies rarely give one | "Shared the project with [org] for feedback" (only if you did) |
| "Used across India" | Visitors from many cities ≠ adoption | "[N] checks; most from [city] workshops" (only if you know) |
| "[N] people trained" counting a crowd you spoke to | Trained implies they learned and practised something | "[N] attendees; [M] completed both quizzes" |
| "Clinically / scientifically proven" | A 5-person test proves nothing statistically | "Usability test with 5 older adults found [problems]; redesign fixed [x of y]" |
| Rounded-up numbers ("100+", "nearly 1,000") | Looks inflated and can't be checked | Exact number with a date |

---

## 4. Common App activity description (150 characters)

The Common App activities section has short fields for position, organisation and a description of up to 150
characters. Verify the current limits in the application itself, because they can change.

**Template:** `[What you built] for [whom]; [hardest real result]; [real reach with numbers]`

Three example versions. Fill every `[ ]` **only from your logs**, delete anything that isn't true yet, and
re-count characters after filling (numbers may be longer than the placeholder):

1. `Built free bot that flags Hindi/English/Hinglish scam texts & explains why in plain words; ran [N] workshops for [N] seniors; [N] messages checked` *(146 characters with placeholders)*
2. `Founder: AI scam-checker for elders in [CITY]. [X]% recall on real test set; tested with [N] seniors (IRB-approved) & redesigned UI from feedback` *(145 with placeholders; use "real test set" only if it is real data)*
3. `Researched multilingual scam detection; trained & compared 3 AI models; taught [N] seniors to spot scams in [N] workshops w/ [ORG]; paper in review` *(147 with placeholders; "paper in review" only once it is actually submitted; "w/ [ORG]" only with their written agreement)*

**Checklist before you submit it:**
- [ ] Every number is in the impact log, with evidence and a date.
- [ ] Words match the evidence: "flagged" not "stopped", "attendees" not "trained", "checks" not "users".
- [ ] You can explain every word in an interview without notes, including how the model works and where it fails.
- [ ] Your adult sponsor or teacher has read it.
