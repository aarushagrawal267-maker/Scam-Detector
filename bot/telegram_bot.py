"""Telegram chat bot: forward a suspicious message, get a verdict.

Setup (5 minutes, free):
  1. In Telegram, message @BotFather, send /newbot, follow the steps.
     It gives you a token like 123456:ABC-DEF...
  2. Put it in an environment variable (NEVER in the code or on GitHub):
        export TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
  3. Run:  python -m bot.telegram_bot

How it works: "long polling". The bot keeps asking Telegram "any new
messages?" (getUpdates), handles each one, and replies (sendMessage). No
public server or domain is needed, so it runs on a laptop or free host.

Privacy:
  * Message text is checked in memory and never saved or logged.
  * For the "Why?" / language buttons we keep the last RESULT (verdict,
    reasons, defanged links), not the message, in memory for 30 minutes.
  * The language choice is kept in memory only (lost on restart).
  * Only anonymous counts go to the stats database.

The update-handling logic (``BotLogic``) is separate from the network code
(``TelegramApi``) so it can be tested without Telegram (see tests/).
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque

from scam_detector import messages as M
from scam_detector import stats
from scam_detector.detector import check_message
from scam_detector.ocr import OcrUnavailable, extract_text

log = logging.getLogger("scam-bot")

MEMORY_SECONDS = 30 * 60
PER_CHAT_LIMIT = 20  # checks per minute per chat

TEXT = {
    "welcome": {
        "en": (
            "🙏 Namaste! I check messages for scams.\n\n"
            "👉 Just FORWARD me any message you are unsure about (or a screenshot).\n"
            "I will reply: 🔴 SCAM, 🟡 SUSPICIOUS or 🟢 LIKELY SAFE, and tell you why.\n\n"
            "I can be wrong. Lost money? Call 1930."
        ),
        "hi": (
            "🙏 नमस्ते! मैं मैसेज में धोखे की जांच करता हूँ।\n\n"
            "👉 जिस मैसेज पर शक हो, उसे मुझे फॉरवर्ड करें (या स्क्रीनशॉट भेजें)।\n"
            "मैं बताऊँगा: 🔴 धोखा, 🟡 संदिग्ध या 🟢 शायद सुरक्षित, और क्यों।\n\n"
            "मैं गलत भी हो सकता हूँ। पैसे गए? 1930 पर कॉल करें।"
        ),
    },
    "voice": {
        "en": "🎤 I can't listen to voice notes yet. Please type what the caller said, or forward the text message.",
        "hi": "🎤 मैं अभी वॉइस नोट नहीं सुन सकता। कृपया कॉल करने वाले ने जो कहा वह लिखकर भेजें, या मैसेज फॉरवर्ड करें।",
    },
    "unsupported": {
        "en": "Please send the message as text or a screenshot.",
        "hi": "कृपया मैसेज टेक्स्ट या स्क्रीनशॉट के रूप में भेजें।",
    },
    "ocr_missing": {
        "en": "I can't read screenshots right now. Please copy and paste the message text.",
        "hi": "मैं अभी स्क्रीनशॉट नहीं पढ़ सकता। कृपया मैसेज का टेक्स्ट कॉपी करके भेजें।",
    },
    "ocr_empty": {
        "en": "I couldn't find text in that picture. Please send a clearer screenshot or paste the text.",
        "hi": "उस तस्वीर में मुझे टेक्स्ट नहीं मिला। कृपया साफ़ स्क्रीनशॉट भेजें या टेक्स्ट पेस्ट करें।",
    },
    "too_many": {
        "en": "Too many messages. Please wait a minute.",
        "hi": "बहुत सारे मैसेज। कृपया एक मिनट रुकें।",
    },
    "expired": {
        "en": "That result has expired. Please forward the message again.",
        "hi": "वह जवाब पुराना हो गया। कृपया मैसेज फिर से फॉरवर्ड करें।",
    },
    "thanks_wrong": {
        "en": "Thank you! This helps us improve. If you lost money, call 1930 now.",
        "hi": "धन्यवाद! इससे हमें सुधार में मदद मिलेगी। पैसे गए हों तो अभी 1930 पर कॉल करें।",
    },
    "thanks_right": {"en": "Thank you for telling us! 🙏", "hi": "बताने के लिए धन्यवाद! 🙏"},
    "lang_set": {"en": "Language: English ✅", "hi": "भाषा: हिंदी ✅"},
    "privacy": {
        "en": (
            "🔒 Privacy: I do not save your messages or pictures. I only count how many checks "
            "happen (for example '10 scams found today'), with no names or numbers."
        ),
        "hi": (
            "🔒 गोपनीयता: मैं आपके मैसेज या तस्वीरें सेव नहीं करता। मैं सिर्फ़ गिनती रखता हूँ "
            "(जैसे 'आज 10 धोखे मिले'), बिना नाम या नंबर के।"
        ),
    },
    "wrong_btn": {"en": "Was this wrong?", "hi": "क्या यह गलत है?"},
    "right_btn": {"en": "👍 Helpful", "hi": "👍 मददगार"},
    "other_lang": {"en": "हिंदी में", "hi": "In English"},
}


def tr(key: str, lang: str) -> str:
    return TEXT[key].get(lang) or TEXT[key]["en"]


def keyboard(lang: str) -> dict:
    other = "hi" if lang == "en" else "en"
    return {
        "inline_keyboard": [
            [
                {"text": "❓ " + M.UI["why"][lang], "callback_data": "why"},
                {"text": "✅ " + M.UI["what_to_do"][lang], "callback_data": "todo"},
            ],
            [
                {"text": tr("right_btn", lang), "callback_data": "right"},
                {"text": "⚠️ " + tr("wrong_btn", lang), "callback_data": "wrong"},
            ],
            [{"text": "🌐 " + tr("other_lang", lang), "callback_data": f"lang:{other}"}],
        ]
    }


def lang_keyboard() -> dict:
    return {"inline_keyboard": [[{"text": "English", "callback_data": "lang:en"},
                                 {"text": "हिंदी", "callback_data": "lang:hi"}]]}


def why_text(result: dict) -> str:
    lang = result["reply_language"]
    lines = [f"{result['emoji']} {result['label']}", ""]
    flags = result["red_flags"] or [{"text": M.UI["no_flags"][lang]}]
    lines += ["• " + f["text"] for f in flags]
    for link in result["links"]:
        lines.append(f"\n🔗 {link['url']}: {link['risk_label']}")
        lines += ["   - " + r for r in link["reason_text"]]
    return "\n".join(lines)


def todo_text(result: dict) -> str:
    return "\n".join(f"{i}. {a}" for i, a in enumerate(result["advice"], 1)) + "\n\nℹ️ " + result["disclaimer"]


class BotLogic:
    """All decisions, no networking. ``api`` must provide send(), answer(), file_bytes()."""

    def __init__(self, api, record_stats: bool = True):
        self.api = api
        self.record_stats = record_stats
        self.lang: dict[int, str] = {}
        self.last: dict[int, tuple[float, dict]] = {}  # chat -> (time, {"en": result, "hi": result})
        self.hits: dict[int, deque] = defaultdict(deque)

    # ------------------------------------------------------------ helpers --
    def _lang(self, chat: int, guess: str | None = None) -> str:
        return self.lang.get(chat) or guess or "hi"

    def _limited(self, chat: int) -> bool:
        now = time.monotonic()
        q = self.hits[chat]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= PER_CHAT_LIMIT:
            return True
        q.append(now)
        return False

    def _forget_old(self) -> None:
        cutoff = time.time() - MEMORY_SECONDS
        for chat in [c for c, (t, _) in self.last.items() if t < cutoff]:
            del self.last[chat]

    # ------------------------------------------------------------- checks --
    def _check_and_reply(self, chat: int, text: str, channel: str) -> None:
        # Compute both languages now so the language button works without keeping the message.
        res = {lg: check_message(text, lang=lg) for lg in M.LANGS}
        chosen = self.lang.get(chat)
        if chosen is None:  # first time: guess from the message, user can switch
            chosen = res["en"]["reply_language"] if res["en"]["language_detected"] == "en" else "hi"
        self.last[chat] = (time.time(), res)
        r = res[chosen]
        self.api.send(chat, r["reply_text"], keyboard(chosen))
        if self.record_stats:
            stats.record_check(r["verdict"], r["category"], r["language_detected"], channel)
            stats.record_user(f"tg:{chat}")

    def handle(self, update: dict) -> None:
        self._forget_old()
        if "callback_query" in update:
            return self._callback(update["callback_query"])
        msg = update.get("message") or update.get("edited_message")
        if not msg:
            return
        chat = msg["chat"]["id"]
        lang = self._lang(chat)
        text = msg.get("text") or msg.get("caption")

        if text and text.strip().startswith("/"):
            cmd = text.strip().split()[0].split("@")[0].lower()
            if cmd in ("/start", "/help"):
                self.api.send(chat, tr("welcome", "en") + "\n\n" + tr("welcome", "hi"), lang_keyboard())
            elif cmd in ("/language", "/bhasha"):
                self.api.send(chat, "Choose language / भाषा चुनें", lang_keyboard())
            elif cmd == "/privacy":
                self.api.send(chat, tr("privacy", lang))
            return

        if self._limited(chat):
            self.api.send(chat, tr("too_many", lang))
            return

        if msg.get("photo"):
            file_id = msg["photo"][-1]["file_id"]  # largest size
            try:
                extracted = extract_text(self.api.file_bytes(file_id))
            except OcrUnavailable:
                self.api.send(chat, tr("ocr_missing", lang))
                return
            except Exception:
                self.api.send(chat, tr("ocr_empty", lang))
                return
            combined = " ".join(x for x in (extracted, msg.get("caption")) if x)
            if len(combined.strip()) < 5:
                self.api.send(chat, tr("ocr_empty", lang))
                return
            return self._check_and_reply(chat, combined, "telegram-image")

        if msg.get("voice") or msg.get("audio") or msg.get("video_note"):
            self.api.send(chat, tr("voice", lang))
            return

        if text:
            return self._check_and_reply(chat, text, "telegram")

        self.api.send(chat, tr("unsupported", lang))

    def _callback(self, cq: dict) -> None:
        chat = cq["message"]["chat"]["id"]
        data = cq.get("data", "")
        self.api.answer(cq["id"])
        if data.startswith("lang:"):
            new = data.split(":", 1)[1]
            if new not in M.LANGS:
                return
            self.lang[chat] = new
            if chat in self.last:
                r = self.last[chat][1][new]
                self.api.send(chat, r["reply_text"], keyboard(new))
            else:
                self.api.send(chat, tr("lang_set", new) + "\n\n" + tr("welcome", new))
            return
        lang = self._lang(chat)
        if chat not in self.last:
            self.api.send(chat, tr("expired", lang))
            return
        r = self.last[chat][1][lang]
        if data == "why":
            self.api.send(chat, why_text(r))
        elif data == "todo":
            self.api.send(chat, todo_text(r))
        elif data in ("wrong", "right"):
            if self.record_stats:
                stats.record_feedback(r["verdict"], "wrong" if data == "wrong" else "correct")
            self.api.send(chat, tr("thanks_wrong" if data == "wrong" else "thanks_right", lang))


class TelegramApi:
    """Thin wrapper around the Telegram Bot HTTP API."""

    def __init__(self, token: str):
        import httpx

        self.base = f"https://api.telegram.org/bot{token}"
        self.file_base = f"https://api.telegram.org/file/bot{token}"
        self.http = httpx.Client(timeout=40)

    def call(self, method: str, **params) -> dict:
        r = self.http.post(f"{self.base}/{method}", json=params)
        r.raise_for_status()
        return r.json()

    def send(self, chat: int, text: str, markup: dict | None = None) -> None:
        params = {"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True}
        if markup:
            params["reply_markup"] = markup
        self.call("sendMessage", **params)

    def answer(self, callback_id: str) -> None:
        self.call("answerCallbackQuery", callback_query_id=callback_id)

    def file_bytes(self, file_id: str) -> bytes:
        info = self.call("getFile", file_id=file_id)["result"]
        if info.get("file_size", 0) > 6 * 1024 * 1024:
            raise ValueError("file too large")
        return self.http.get(f"{self.file_base}/{info['file_path']}").content

    def updates(self, offset: int | None) -> list[dict]:
        return self.call("getUpdates", offset=offset, timeout=30,
                         allowed_updates=["message", "callback_query"]).get("result", [])


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("Set the TELEGRAM_BOT_TOKEN environment variable first (see the top of this file).")
    api = TelegramApi(token)
    api.call("setMyCommands", commands=[
        {"command": "start", "description": "How to use / कैसे इस्तेमाल करें"},
        {"command": "language", "description": "English / हिंदी"},
        {"command": "privacy", "description": "Privacy / गोपनीयता"},
    ])
    logic = BotLogic(api)
    offset = None
    log.info("Bot running. Press Ctrl+C to stop.")
    while True:
        try:
            for upd in api.updates(offset):
                offset = upd["update_id"] + 1
                try:
                    logic.handle(upd)
                except Exception as e:  # never crash on one bad message; never log its text
                    log.warning("failed to handle update: %s", type(e).__name__)
        except KeyboardInterrupt:
            break
        except Exception as e:  # network hiccup: wait and retry
            log.warning("polling error: %s; retrying in 5s", type(e).__name__)
            time.sleep(5)


if __name__ == "__main__":
    main()
