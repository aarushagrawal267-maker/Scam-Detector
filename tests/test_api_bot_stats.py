import io
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import server
from bot.telegram_bot import BotLogic
from scam_detector import stats
from scam_detector.ocr import ocr_available

SECRET_TEXT = "Zqxjv-unique-token: your SBI account will be blocked, share OTP now"


@pytest.fixture
def client(monkeypatch):
    server._hits.clear()
    return TestClient(server.app)


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"


def test_check_endpoint(client):
    r = client.post("/api/check", json={"text": SECRET_TEXT, "lang": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] in {"scam", "suspicious"}
    assert r.headers["Content-Security-Policy"].startswith("default-src 'self'")


def test_empty_check_is_rejected(client):
    assert client.post("/api/check", json={"text": "  "}).status_code in (400, 422)


def test_feedback_and_stats(client):
    client.post("/api/check", json={"text": SECRET_TEXT})
    assert client.post("/api/feedback", json={"verdict": "scam", "kind": "correct"}).json() == {"ok": True}
    assert client.post("/api/feedback", json={"verdict": "scam", "kind": "nonsense"}).status_code == 400
    s = client.get("/api/stats").json()
    assert s["total_checks"] == 1
    # Public view hides groups smaller than 5.
    assert "other (small groups hidden)" in s["by_verdict"]


def test_private_stats_need_token(client, monkeypatch):
    assert client.get("/api/stats?public=0").status_code == 403
    monkeypatch.setenv("ADMIN_TOKEN", "letmein")
    ok = client.get("/api/stats?public=0", headers={"X-Admin-Token": "letmein"})
    assert ok.status_code == 200


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(server, "RATE_LIMIT", 3)
    codes = [client.post("/api/check", json={"text": "hello there"}).status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and codes[3] == 429


@pytest.mark.skipif(not ocr_available(), reason="Tesseract not installed")
def test_screenshot_check(client):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1200, 200), "white")
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 36)
    except OSError:
        font = ImageFont.load_default()
    ImageDraw.Draw(img).text((20, 60), "Your account will be blocked. Share OTP now", fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    r = client.post("/api/check-image", files={"file": ("s.png", buf.getvalue(), "image/png")}, data={"lang": "en"})
    assert r.status_code == 200, r.text
    assert "OTP" in r.json()["extracted_text"]


def test_stats_db_never_contains_message_text(client, temp_stats_db):
    client.post("/api/check", json={"text": SECRET_TEXT})
    bot = BotLogic(FakeApi())
    bot.handle({"update_id": 1, "message": {"chat": {"id": 42}, "text": SECRET_TEXT}})
    raw = temp_stats_db.read_bytes()
    assert b"Zqxjv" not in raw and b"share OTP" not in raw
    assert b"tg:42" not in raw  # the raw chat id is never stored, only a keyed hash
    conn = sqlite3.connect(temp_stats_db)
    users = conn.execute("SELECT user_hash FROM weekly_users").fetchall()
    assert len(users) == 1 and len(users[0][0]) == 16


def test_weekly_users_are_counted_once():
    stats.record_user("tg:1")
    stats.record_user("tg:1")
    stats.record_user("tg:2")
    assert stats.summary()["weekly_bot_users"][-1]["users"] == 2


class FakeApi:
    def __init__(self):
        self.sent = []

    def send(self, chat, text, markup=None):
        self.sent.append((chat, text, markup))

    def answer(self, callback_id):
        pass

    def file_bytes(self, file_id):
        raise AssertionError("not used")


def test_bot_flow():
    api = FakeApi()
    bot = BotLogic(api)
    bot.handle({"update_id": 1, "message": {"chat": {"id": 7}, "text": "/start"}})
    assert "FORWARD" in api.sent[-1][1]

    bot.handle({"update_id": 2, "message": {"chat": {"id": 7}, "text": "Hi mom this is my new number, send 10000 urgently"}})
    chat, text, markup = api.sent[-1]
    assert text.startswith(("🔴", "🟡"))
    assert markup["inline_keyboard"][0][0]["callback_data"] == "why"

    cb = {"id": "x", "message": {"chat": {"id": 7}}}
    bot.handle({"update_id": 3, "callback_query": {**cb, "data": "why"}})
    assert "•" in api.sent[-1][1]
    bot.handle({"update_id": 4, "callback_query": {**cb, "data": "lang:en"}})
    assert "SCAM" in api.sent[-1][1] or "SUSPICIOUS" in api.sent[-1][1]
    bot.handle({"update_id": 5, "callback_query": {**cb, "data": "todo"}})
    assert "1930" in api.sent[-1][1]
    bot.handle({"update_id": 6, "callback_query": {**cb, "data": "wrong"}})
    assert stats.summary()["feedback"]["wrong"] == 1


def test_bot_voice_note_gets_helpful_reply():
    api = FakeApi()
    BotLogic(api).handle({"update_id": 1, "message": {"chat": {"id": 9}, "voice": {"file_id": "v"}}})
    assert "🎤" in api.sent[-1][1]
