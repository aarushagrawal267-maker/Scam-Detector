"""Web server: the website + a small JSON API.

Run locally:
    uvicorn app.server:app --reload
then open http://127.0.0.1:8000

API
---
POST /api/check        {"text": "...", "lang": "en"|"hi"|null}         -> result
POST /api/check-image  multipart form: file=<image>, lang=en|hi        -> {"extracted_text", "result"}
POST /api/feedback     {"verdict": "...", "kind": "correct"|"wrong"|"helpful"|"not_helpful"}
GET  /api/stats        ?public=1 hides small groups                      -> counts
GET  /api/health

Privacy: message text and images are processed in memory and never written to
disk or logs. Only anonymous counts are stored (see scam_detector/stats.py).
"""

from __future__ import annotations

import hmac
import os
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.formparsers import MultiPartParser

from scam_detector import __version__, stats
from scam_detector.detector import MAX_CHARS, check_message
from scam_detector.model import load_meta, load_model
from scam_detector.ocr import MAX_BYTES as MAX_IMAGE_BYTES
from scam_detector.ocr import OcrUnavailable, extract_text, ocr_available

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="AI Scam Message Detector", version=__version__, docs_url="/api/docs", redoc_url=None)


# ---------------------------------------------------------------- safety ----
RATE_LIMIT = 30  # requests per minute per IP, for the /api/check* endpoints
_hits: dict[str, deque] = defaultdict(deque)
_MAX_TRACKED_IPS = 10_000  # forget old entries so memory can't grow forever

# A screenshot upload may be at most the OCR limit plus a little room for the
# form fields. Bigger requests are refused before they are read.
MAX_UPLOAD_REQUEST = MAX_IMAGE_BYTES + 64 * 1024
# Keep uploaded screenshots in memory: by default Starlette writes uploads
# bigger than 1 MB to a temporary file on disk, which would break the
# "images are never written to disk" privacy promise.
MultiPartParser.spool_max_size = MAX_UPLOAD_REQUEST


def _rate_limited(request: Request) -> bool:
    """Very small in-memory rate limiter to stop one person flooding the server.

    The IP address is only kept in memory for 60 seconds and never stored.
    """
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    if len(_hits) > _MAX_TRACKED_IPS:
        for key in [k for k, v in _hits.items() if not v or now - v[-1] > 60]:
            del _hits[key]
    q = _hits[ip]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return True
    q.append(now)
    return False


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if request.url.path.startswith("/api/check") and _rate_limited(request):
        return JSONResponse({"error": "Too many checks. Please wait a minute."}, status_code=429)
    if request.url.path == "/api/check-image" and request.method == "POST":
        length = request.headers.get("content-length")
        if length is None or not length.isdigit():
            return JSONResponse({"detail": "Upload size missing."}, status_code=411)
        if int(length) > MAX_UPLOAD_REQUEST:
            return JSONResponse({"detail": "Image is too large (max 6 MB)."}, status_code=413)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    if not request.url.path.startswith("/api/docs"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
    return response


# ------------------------------------------------------------------ API -----
class CheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_CHARS * 2)
    lang: str | None = None


class FeedbackRequest(BaseModel):
    verdict: str
    kind: str


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": __version__,
        "model_loaded": load_model() is not None,
        "model_version": load_meta().get("model_version"),
        "ocr_available": ocr_available(),
    }


@app.post("/api/check")
def api_check(req: CheckRequest):
    try:
        result = check_message(req.text, lang=req.lang)
    except ValueError:
        raise HTTPException(400, "Please paste a message to check.")
    stats.record_check(result["verdict"], result["category"], result["language_detected"], "web")
    return result


@app.post("/api/check-image")
async def api_check_image(file: UploadFile = File(...), lang: str | None = Form(None)):
    if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(415, "Please upload a PNG, JPG or WebP screenshot.")
    data = await file.read()
    try:
        text = extract_text(data)
    except OcrUnavailable:
        raise HTTPException(501, "Screenshot reading is not available on this server. Please paste the text instead.")
    except ValueError as e:
        raise HTTPException(413, str(e))
    except Exception:
        raise HTTPException(400, "Could not read that image. Please try a clearer screenshot or paste the text.")
    finally:
        del data
    if len(text.strip()) < 5:
        raise HTTPException(422, "No text found in the image. Please paste the message text instead.")
    result = check_message(text, lang=lang)
    stats.record_check(result["verdict"], result["category"], result["language_detected"], "web-image")
    return {"extracted_text": text, "result": result}


@app.post("/api/feedback")
def api_feedback(req: FeedbackRequest):
    if req.verdict not in {"scam", "suspicious", "likely_safe"}:
        raise HTTPException(400, "bad verdict")
    try:
        stats.record_feedback(req.verdict, req.kind)
    except ValueError:
        raise HTTPException(400, "bad feedback kind")
    return {"ok": True}


@app.get("/api/stats")
def api_stats(request: Request, public: int = 1):
    """Public stats for everyone; the full (private) view needs the admin token.

    Set ADMIN_TOKEN in the server's environment and send it as the
    ``X-Admin-Token`` header to see small groups too.
    """
    if not public:
        expected = os.environ.get("ADMIN_TOKEN")
        given = request.headers.get("X-Admin-Token", "")
        if not expected or not hmac.compare_digest(expected, given):
            raise HTTPException(403, "Admin token required for the private dashboard.")
    return stats.summary(public=bool(public))


# --------------------------------------------------------------- website ----
@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
