"""Security regression tests: input size limits, slow-regex inputs, OCR limits,
no secrets in logs. Each test fails on the code before the matching fix."""

import io
import logging
import subprocess
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from app import server
from bot import telegram_bot
from bot.telegram_bot import BotLogic, TelegramApi
from scam_detector import ocr
from scam_detector.detector import check_message
from scam_detector.text_utils import find_urls


@pytest.fixture
def client():
    server._hits.clear()
    return TestClient(server.app)


# ------------------------------------------------------- request bodies ----
def test_big_json_body_is_refused_by_length(client):
    body = b'{"text": "' + b"a" * (server.MAX_JSON_REQUEST + 10) + b'"}'
    r = client.post("/api/check", content=body, headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_big_json_body_without_length_is_refused(client):
    # A chunked upload has no Content-Length; the bytes are counted as they arrive.
    def chunks():
        yield b'{"text": "'
        for _ in range(20):
            yield b"a" * 8192
        yield b'"}'

    r = client.post("/api/check", content=chunks(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413


def test_normal_sized_json_still_works(client):
    r = client.post("/api/check", json={"text": "Your parcel is held, pay Rs 25 at indiapost-help.xyz " * 50})
    assert r.status_code == 200


def test_feedback_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(server, "RATE_LIMIT", 3)
    codes = [client.post("/api/feedback", json={"verdict": "scam", "kind": "correct"}).status_code
             for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and codes[3] == 429


# ------------------------------------------------------------ slow regex ---
@pytest.mark.parametrize("text", ["a." * 2500, "a-" * 2500, "aa." * 1666, ("a" * 70 + ".") * 70])
def test_link_finder_is_fast_on_adversarial_text(text):
    check_message("warm up the model")
    start = time.perf_counter()
    check_message(text)
    # Was about 1 second (link regex backtracking) per 5,000 characters.
    assert time.perf_counter() - start < 0.5


def test_link_finder_still_finds_links():
    assert find_urls("Pay at sbi-kyc.xyz/abc or https://bit.ly/x now. secure.sbi.co.in") == [
        "sbi-kyc.xyz/abc", "https://bit.ly/x", "secure.sbi.co.in"
    ]


# ------------------------------------------------------------------- OCR ---
def _png(size, mode="L"):
    from PIL import Image

    buf = io.BytesIO()
    Image.new(mode, size, 255).save(buf, format="PNG")
    return buf.getvalue()


def test_thin_image_is_not_enlarged_past_the_pixel_limit():
    # 2 x 8,000,000 pixels: a 23 KB file. The old "enlarge to 1000 px wide" step
    # asked for a 1000 x 4,000,000,000 pixel image.
    img = ocr._prepare(_png((2, 8_000_000)))
    assert img.width * img.height <= ocr.MAX_PIXELS


def test_small_screenshots_are_still_enlarged():
    img = ocr._prepare(_png((500, 300)))
    assert img.size == (1000, 600)


def test_only_png_jpeg_webp_are_decoded():
    from PIL import Image, UnidentifiedImageError

    buf = io.BytesIO()
    Image.new("L", (50, 50), 255).save(buf, format="TIFF")
    with pytest.raises(UnidentifiedImageError):
        ocr._prepare(buf.getvalue())


@pytest.mark.skipif(not ocr.ocr_available(), reason="Tesseract not installed")
def test_ocr_never_writes_the_image_to_disk(monkeypatch):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (900, 120), "white")
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 36)
    except OSError:
        font = ImageFont.load_default()
    ImageDraw.Draw(img).text((10, 40), "Share your OTP now", fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    real_save = Image.Image.save

    def save_only_to_memory(self, fp, *args, **kwargs):
        assert not isinstance(fp, (str, bytes)) and not hasattr(fp, "__fspath__"), "image saved to a file"
        return real_save(self, fp, *args, **kwargs)

    monkeypatch.setattr(Image.Image, "save", save_only_to_memory)
    assert "OTP" in ocr.extract_text(buf.getvalue())


def test_slow_ocr_is_stopped(client, monkeypatch):
    def too_slow(*args, **kwargs):
        assert kwargs.get("timeout"), "tesseract must run with a timeout"
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])

    monkeypatch.setattr(ocr, "ocr_available", lambda: True)
    monkeypatch.setattr(ocr.subprocess, "run", too_slow)
    r = client.post("/api/check-image", files={"file": ("s.png", _png((300, 100)), "image/png")})
    assert r.status_code == 400


# ------------------------------------------------------------ Telegram bot --
TOKEN = "123456:SECRET-bot-token"


def _api(handler) -> TelegramApi:
    api = TelegramApi(TOKEN)
    api.http = httpx.Client(transport=httpx.MockTransport(handler))
    return api


def test_bot_token_is_not_written_to_logs(caplog):
    api = _api(lambda req: httpx.Response(200, json={"ok": True, "result": []}))
    old = {n: logging.getLogger(n).level for n in ("httpx", "httpcore")}
    try:
        telegram_bot.quiet_http_logs()
        with caplog.at_level(logging.DEBUG):
            api.updates(None)
    finally:
        for name, level in old.items():
            logging.getLogger(name).setLevel(level)
    assert "SECRET" not in caplog.text


def test_bot_photo_download_is_capped_without_file_size():
    def handler(req):
        if req.url.path.endswith("/getFile"):
            return httpx.Response(200, json={"ok": True, "result": {"file_path": "photos/a.jpg"}})
        return httpx.Response(200, content=b"\0" * (telegram_bot.MAX_PHOTO_BYTES + 1))

    with pytest.raises(ValueError):
        _api(handler).file_bytes("abc")


def test_bot_forgets_idle_chats():
    class Api:
        def send(self, *a, **k):
            pass

    bot = BotLogic(Api(), record_stats=False)
    for chat in range(50):
        bot.hits[chat]  # empty entries, as left behind after a minute
    bot.handle({"update_id": 1, "message": {"chat": {"id": 1}, "text": "/start"}})
    assert len(bot.hits) == 0
