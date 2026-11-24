# Deployment: platforms, hosting and running it safely

*Platform rules and prices were checked on 2026-11-17 against the official pages linked below. They change often, so **re-check before you commit to a platform.***

## 1. Which platform should users reach the checker on?

| | **Telegram bot** | **WhatsApp Business Platform (Cloud API)** | **Web app** (this repo's website) | **SMS** |
|---|---|---|---|---|
| **Cost** | Free. Bots can message users *"at no cost"*; paid broadcasts are optional ([Telegram Bot FAQ](https://core.telegram.org/bots/faq)) | Per-message pricing since 1 Jul 2025. Messages users send you are free. **From 1 Oct 2026, replies ("service messages") are charged after 1,000 free per business number per month**, except for *eligible government and non-profit organisations* (until 31 Dec 2027). India-billed accounts must move to INR billing by 31 Dec 2026 ([Meta pricing docs](https://developers.facebook.com/docs/whatsapp/pricing)) | Free to build. Hosting is free or cheap (see §2) | Per-SMS charges plus registration (amounts NOT VERIFIED) |
| **Approval needed** | None. Create a bot with @BotFather in minutes | A Meta business portfolio. New portfolios can message only 250 unique users per rolling 24 h *outside* a customer-service window. Scaling up needs business verification or sending volume ([Meta messaging limits](https://developers.facebook.com/docs/whatsapp/messaging-limits)) | None | Business senders in India must register on TRAI's **DLT** system (entity, sender header and every message template). Source: operator/vendor documentation; TRAI's own text NOT VERIFIED here |
| **AI-chatbot policy** | No restriction found | ⚠️ **Section 4.7 "AI Providers":** providers and developers of AI/ML technologies *"are strictly prohibited"* from using the platform when AI is *"the primary (rather than incidental or ancillary) functionality"*, and **Meta decides in its "sole discretion"** ([Meta Terms for WhatsApp Business Platform](https://www.facebook.com/legal/Meta-Terms-for-WhatsApp-Business-Platform), last modified 23 Sep 2026). A scam checker whose main job is an ML classifier **may or may not** fall under this. It is ambiguous, so get written clarification from Meta or a Business Solution Provider before building on WhatsApp | n/a | n/a |
| **Ease for older users** | Medium-low: many older users in India may not have Telegram. Check this in your pilot | **Highest:** they forward the suspicious message inside the app they already use | Medium-low: they have to copy and paste, or upload a screenshot. A QR code on the printed guide helps | Low: forwarding an SMS to a number is awkward, and replies can't show buttons |
| **Good for** | Prototype and supervised pilot | The final product, *after* the pilot and a policy check | Demos, judges, workshops and the impact page | Not recommended |

### Recommendation

1. **Now to the pilot:** the **web app** (big paste box, screenshot upload, QR code on the printed guide) plus the **Telegram bot** for testers who have Telegram. Both cost nothing.
2. **After pilot results:** consider WhatsApp **only if** all three of these hold:
   - (a) the pilot shows people want it;
   - (b) Meta or a Business Solution Provider confirms *in writing* that a single-purpose scam checker is not barred by Section 4.7;
   - (c) the cost after 1,000 free replies a month is covered. The cleanest route is often through a **partner non-profit or government body**, because eligible ones keep free service messages beyond the free tier until 31 Dec 2027.
3. **Skip SMS.**

## 2. Where to host it (free options, honestly compared)

| Option | Verified facts (2026-11-17) | Problems for *this* app | Verdict |
|---|---|---|---|
| **Your own computer** (or a school computer that stays on) | Free. You control it | Only online while the machine is on. Making the *website* public needs a tunnel service. The Telegram bot needs **no** public URL in polling mode | ✅ **Best for the supervised pilot.** The bot works from home, the stats database persists, and Tesseract is easy to install |
| **Render (free web service)** | Free services *"spin down"* after 15 minutes with no traffic and take *"about one minute"* to wake. 750 free instance hours per month. Python web services are allowed. **No persistent disks**, and the filesystem is *ephemeral* ([Render docs](https://render.com/docs/free)) | **The SQLite stats database (`SCAM_STATS_DB`) is wiped** on every restart, redeploy or spin-down. A 1-minute first load is a bad first impression for older users. A polling bot won't stay alive. Tesseract needs a Docker deploy (free-tier Docker support NOT VERIFIED). Without it, screenshot upload reports "not available" | ⚠️ OK for a **public demo website** only. Don't trust its dashboard numbers |
| **Hugging Face Spaces** | Official docs: *"Gradio and Docker Spaces run on compute and require a paid plan to create… Static Spaces are free for everyone."* CPU Basic hardware (2 vCPU, 16 GB) has no hourly cost, but disk is *not persistent* ([HF Spaces overview](https://huggingface.co/docs/hub/en/spaces-overview)) | This FastAPI app needs a Docker Space, which **now needs a paid PRO plan** | ❌ Not free for this app any more (a static Space could host only the information pages) |
| **PythonAnywhere (free Beginner)** | 1 web app, a "100 seconds" CPU allowance, 512 MB, *restricted* outbound internet (allowlist), **no always-on tasks** ([pricing](https://www.pythonanywhere.com/pricing/)). FastAPI/ASGI hosting is a **beta**, and free-plan support is unconfirmed ([ASGI help](https://help.pythonanywhere.com/pages/ASGICommandLine/)) | The bot can't run, and ASGI on the free plan is uncertain | ❌ Not recommended |

**Bottom line:** for the pilot, run everything on one always-on computer that you or your school control. For judges, a Render free demo works if you **warn people it may take a minute to wake up** and **don't use its stats as impact numbers**.

## 3. Run it locally (step by step)

```bash
git clone https://github.com/aarushagrawal267-maker/scam-detector.git
cd scam-detector
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.server:app --reload
```

Open http://127.0.0.1:8000. Check http://127.0.0.1:8000/api/health: it reports whether the model and OCR are loaded.

### Screenshot reading (OCR) needs Tesseract

- Ubuntu/Debian: `sudo apt install tesseract-ocr tesseract-ocr-hin` (English + Hindi). This is what `scam_detector/ocr.py` expects.
- Windows/macOS: follow the official instructions at https://github.com/tesseract-ocr/tesseract and also install the **Hindi (`hin`)** language data.
- Without Tesseract, the app still works. Screenshot upload just replies that it isn't available.

### Telegram bot

1. In Telegram, open **@BotFather** → `/newbot` → pick a name. BotFather gives you a **token**. Treat it like a password.
2. Put the token in an environment variable (never in code):

   ```bash
   export TELEGRAM_BOT_TOKEN="123456:ABC..."     # Windows PowerShell: $env:TELEGRAM_BOT_TOKEN="..."
   python -m bot.telegram_bot
   ```

3. The bot uses **long polling**: it asks Telegram for new messages. It needs no public URL, but the process must keep running (on an always-on computer).
4. Telegram's limits: in one chat, *"avoid sending more than one message per second"*. Broadcasts are limited to about 30 messages per second ([Telegram Bot FAQ](https://core.telegram.org/bots/faq)).

## 4. Environment variables (configuration and secrets)

| Variable | What it does | Secret? |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Lets the bot log in to Telegram | **Yes** |
| `GOOGLE_SAFE_BROWSING_API_KEY` | Optional: checks links against Google's list of dangerous sites. Only the link is sent, never the message | **Yes** |
| `ADMIN_TOKEN` | Unlocks the private dashboard: `GET /api/stats?public=0` with header `X-Admin-Token: <token>`. Make it long and random | **Yes** |
| `SCAM_STATS_DB` | Where the anonymous-counts SQLite file lives (default `data/stats.db`). Must be on a **persistent** disk | No |
| `SCAM_MODEL_PATH` / `SCAM_MODEL_META` | Optional: use a different trained model file | No |

**Keeping secrets out of git:**
- Put them in a file called `.env` on the server, or in your host's "secrets" settings.
- Make sure `.env` is listed in `.gitignore`.
- Run `git status` before every commit and check that no key appears.
- **If a key is ever pushed to GitHub, treat it as leaked.** Revoke it (BotFather: `/revoke`; Google Cloud console for API keys) and create a new one. Deleting the commit is not enough.

**Google Safe Browsing terms (verified):**
- *"There is no cost for use of this API"*.
- *"The Safe Browsing API is for non-commercial use only"*. A free student or non-profit tool fits. If the project ever becomes commercial, Google points to its **Web Risk** API instead.
- Each developer gets a default quota, visible in the Google Cloud console ([Safe Browsing usage limits](https://developers.google.com/safe-browsing/v4/usage-limits)).

## 5. Docker (any Docker host, e.g. a Render "Docker" web service)

The repository now contains a ready [`Dockerfile`](../Dockerfile). It installs only the runtime packages from `requirements.txt` (not the large training libraries), adds Tesseract with English + Hindi, runs as a non-root user, disables access logs (so IP addresses are not logged) and listens on `$PORT`.

```bash
docker build -t scam-checker .
docker run -p 8000:8000 -e ADMIN_TOKEN=change-me scam-checker
```

To keep the anonymous stats across restarts, mount a volume on `/app/data`, e.g. `-v scam-data:/app/data`.

## 6. Keeping it running: monitoring

- **Health check:** `GET /api/health` returns `status`, `model_loaded` and `ocr_available`. Point a free uptime monitor at it (check the provider's current free plan; NOT VERIFIED here). It should email you if the site goes down.
- **Render note:** pinging a free Render service every few minutes keeps it awake, but uses free hours. One service running all month is about 744 hours, just inside the 750-hour allowance. A second service won't fit.
- **Bot check:** once a day, send the bot a known scam example from `data/challenge/` and confirm it replies 🔴.
- **Write down every outage** (date, cause, fix) in your impact log. Judges value honest reliability notes.

## 7. Basic security checklist

- [ ] **Never log message text.**
  - The app keeps only anonymous counts (`scam_detector/stats.py`).
  - Run uvicorn with `--no-access-log` in production: access logs record users' IP addresses, which the privacy policy says are not stored.
- [ ] **Rate limiting is on:** `app/server.py` allows 30 checks per minute per IP, held in memory only.
  - **Behind a host's proxy** (Render and most clouds), start uvicorn with `--proxy-headers --forwarded-allow-ips="*"`. Otherwise every user appears to have the proxy's IP and they all share one limit.
- [ ] **Private dashboard** (`public=0`) needs `ADMIN_TOKEN`. The public view hides groups smaller than 5.
- [ ] **Uploads are limited** (6 MB, PNG/JPEG/WebP, decompression-bomb guard) and never saved to disk.
- [ ] **Only load model files you trained yourself.** `joblib.load` can run hidden code.
- [ ] **Secrets only in environment variables.** Rotate them immediately if leaked.
- [ ] **Errors stay polite:** users see a plain message ("Please paste the text instead"), never a stack trace.
- [ ] **Safety wording stays on every result:** no guarantee; 🟢 is not proof of safety; 1930 / cybercrime.gov.in / Chakshu at sancharsaathi.gov.in. The Chakshu wording was checked on the [official page](https://sancharsaathi.gov.in/sfc/) on 2026-11-17.
