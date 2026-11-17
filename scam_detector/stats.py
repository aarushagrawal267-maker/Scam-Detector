"""Anonymous usage statistics for the impact dashboard.

Privacy by design:
  * We store COUNTS only: "on 2026-11-17, 3 web checks were SCAM / fake_bank_kyc / hi".
  * We never store the message text, the image, phone numbers, IP addresses or
    exact times.
  * "Weekly users" for the chat bot uses a one-way keyed hash of the chat id with
    a secret that changes every week, so users cannot be followed across weeks
    and the hash cannot be turned back into a chat id.
  * The public stats view hides any group with fewer than 5 checks, so a tiny
    group can't point to one person.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("SCAM_STATS_DB", ROOT / "data" / "stats.db"))
MIN_PUBLIC_COUNT = 5

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS checks (
    day TEXT, verdict TEXT, category TEXT, language TEXT, channel TEXT, n INTEGER,
    PRIMARY KEY (day, verdict, category, language, channel)
);
CREATE TABLE IF NOT EXISTS feedback (
    day TEXT, verdict TEXT, kind TEXT, n INTEGER,
    PRIMARY KEY (day, verdict, kind)
);
CREATE TABLE IF NOT EXISTS weekly_users (
    week TEXT, user_hash TEXT,
    PRIMARY KEY (week, user_hash)
);
CREATE TABLE IF NOT EXISTS week_secrets (week TEXT PRIMARY KEY, secret TEXT);
CREATE TABLE IF NOT EXISTS workshops (
    day TEXT, organisation_type TEXT, participants INTEGER, language TEXT
);
"""

FEEDBACK_KINDS = {"correct", "wrong", "helpful", "not_helpful"}


def _connect(path: Path | None = None) -> sqlite3.Connection:
    path = Path(path or DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(_SCHEMA)
    return conn


def _today() -> str:
    return dt.date.today().isoformat()


def _week() -> str:
    y, w, _ = dt.date.today().isocalendar()
    return f"{y}-W{w:02d}"


def record_check(verdict: str, category: str | None, language: str, channel: str, db: Path | None = None) -> None:
    with _lock, _connect(db) as conn:
        conn.execute(
            """INSERT INTO checks VALUES (?,?,?,?,?,1)
               ON CONFLICT(day,verdict,category,language,channel) DO UPDATE SET n=n+1""",
            (_today(), verdict, category or "none", language, channel),
        )


def record_feedback(verdict: str, kind: str, db: Path | None = None) -> None:
    if kind not in FEEDBACK_KINDS:
        raise ValueError(f"unknown feedback kind {kind!r}")
    with _lock, _connect(db) as conn:
        conn.execute(
            """INSERT INTO feedback VALUES (?,?,?,1)
               ON CONFLICT(day,verdict,kind) DO UPDATE SET n=n+1""",
            (_today(), verdict, kind),
        )


def record_user(raw_user_id: str, db: Path | None = None) -> None:
    """Count a weekly active bot user without storing who they are."""
    week = _week()
    with _lock, _connect(db) as conn:
        row = conn.execute("SELECT secret FROM week_secrets WHERE week=?", (week,)).fetchone()
        if row is None:
            secret = secrets.token_hex(32)
            conn.execute("INSERT INTO week_secrets VALUES (?,?)", (week, secret))
            # Forget older secrets so old hashes can never be recomputed.
            conn.execute("DELETE FROM week_secrets WHERE week<>?", (week,))
        else:
            secret = row[0]
        digest = hmac.new(secret.encode(), str(raw_user_id).encode(), hashlib.sha256).hexdigest()[:16]
        conn.execute("INSERT OR IGNORE INTO weekly_users VALUES (?,?)", (week, digest))


def record_workshop(day: str, organisation_type: str, participants: int, language: str, db: Path | None = None) -> None:
    """Log a workshop you ran (entered by you, from your impact log)."""
    with _lock, _connect(db) as conn:
        conn.execute("INSERT INTO workshops VALUES (?,?,?,?)", (day, organisation_type, int(participants), language))


def summary(public: bool = False, db: Path | None = None) -> dict:
    """Totals for the dashboard. ``public=True`` hides groups smaller than 5."""
    with _lock, _connect(db) as conn:
        total = conn.execute("SELECT COALESCE(SUM(n),0) FROM checks").fetchone()[0]

        def grouped(col: str) -> dict:
            rows = conn.execute(f"SELECT {col}, SUM(n) FROM checks GROUP BY {col} ORDER BY 2 DESC").fetchall()
            out: dict[str, int] = {}
            hidden = 0
            for key, n in rows:
                if public and n < MIN_PUBLIC_COUNT:
                    hidden += n
                else:
                    out[key] = n
            if hidden:
                out["other (small groups hidden)"] = hidden
            return out

        by_day = [
            {"date": d, "count": n}
            for d, n in conn.execute("SELECT day, SUM(n) FROM checks GROUP BY day ORDER BY day DESC LIMIT 60")
        ][::-1]
        fb = dict(conn.execute("SELECT kind, SUM(n) FROM feedback GROUP BY kind").fetchall())
        weekly = [
            {"week": w, "users": n}
            for w, n in conn.execute(
                "SELECT week, COUNT(*) FROM weekly_users GROUP BY week ORDER BY week DESC LIMIT 12"
            )
        ][::-1]
        ws = conn.execute("SELECT COUNT(*), COALESCE(SUM(participants),0) FROM workshops").fetchone()

    rated = fb.get("correct", 0) + fb.get("wrong", 0)
    return {
        "total_checks": total,
        "by_verdict": grouped("verdict"),
        "by_category": grouped("category"),
        "by_language": grouped("language"),
        "by_channel": grouped("channel"),
        "by_day": by_day,
        "weekly_bot_users": weekly,
        "feedback": {k: fb.get(k, 0) for k in sorted(FEEDBACK_KINDS)},
        "user_reported_accuracy": round(fb.get("correct", 0) / rated, 3) if rated else None,
        "user_reported_accuracy_n": rated,
        "workshops": {"count": ws[0], "participants": ws[1]},
        "note": "Counts only. No message text, images, phone numbers or IP addresses are stored.",
    }
