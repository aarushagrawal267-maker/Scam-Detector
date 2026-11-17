"""The heart of the project: turn a message into a verdict + reasons + advice.

Pipeline for one message
------------------------
1. Clean the text and guess its language (English / Hindi / Hinglish).
2. Find links and score each one (never opening them).
3. Run the red-flag rules (rules.py).
4. Ask the ML model for a scam probability (model.py).
5. Combine:   risk = max(model probability, rule score)
   Taking the maximum means EITHER the model OR a strong rule can raise the
   alarm. That is deliberate: missing a scam (false negative) can cost someone
   their savings, while a false alarm only costs them a phone call to check.
6. Compare risk with two thresholds chosen on the validation set:
       risk >= scam threshold        -> SCAM
       risk >= suspicious threshold  -> SUSPICIOUS
       otherwise                     -> LIKELY SAFE (never "safe")
7. Build the plain-language reply.
"""

from __future__ import annotations

from . import messages as M
from .model import load_meta, scam_probability, thresholds
from .rules import RULES, combine_with_url_risk, find_red_flags, pick_category
from .text_utils import detect_language, find_urls, normalise
from .urls import analyse_url, check_safe_browsing

MAX_CHARS = 5000


def verdict_for(risk: float, th: dict | None = None) -> str:
    th = th or thresholds()
    if risk >= th["scam"]:
        return "scam"
    if risk >= th["suspicious"]:
        return "suspicious"
    return "likely_safe"


def score_texts(texts: list[str], use_model: bool = True, use_rules: bool = True) -> list[dict]:
    """Batch scoring used by the evaluation scripts (no reply text, no network)."""
    clean = [normalise(t)[:MAX_CHARS] for t in texts]
    probs = scam_probability(clean) if use_model else None
    out = []
    for i, text in enumerate(clean):
        rule_score = 0.0
        if use_rules:
            rr = find_red_flags(text)
            url_risks = [analyse_url(u).risk for u in find_urls(text)]
            rr = combine_with_url_risk(rr, url_risks)
            rule_score = rr.score
        p = probs[i] if probs is not None else None
        risk = max(p or 0.0, rule_score)
        out.append({"model_probability": p, "rule_score": rule_score, "risk": risk})
    return out


def check_message(text: str, lang: str | None = None, online_link_check: bool = True) -> dict:
    """Check one message and return everything the website / bot needs to reply."""
    clean = normalise(text)[:MAX_CHARS]
    if not clean:
        raise ValueError("empty message")

    detected = detect_language(clean)
    if lang not in M.LANGS:
        # The message was written by the sender, not the user, so this is only a
        # guess at the user's language. Users can switch language at any time.
        lang = "hi" if detected in ("hi", "hinglish") else "en"

    # Links
    url_reports = [analyse_url(u) for u in find_urls(clean)]
    if online_link_check:
        check_safe_browsing(url_reports)

    # Rules + model
    rr = find_red_flags(clean)
    rr = combine_with_url_risk(rr, [r.risk for r in url_reports])
    probs = scam_probability([clean])
    p = probs[0] if probs else None
    risk = max(p or 0.0, rr.score)
    verdict = verdict_for(risk)

    # Strongest warning signs first, so the short chat reply shows the best two.
    weight = {r.id: r.weight for r in RULES} | {"risky_link": 0.55, "unusual_link": 0.3}
    flags = sorted(rr.flags, key=lambda f: -weight.get(f, 0))
    if verdict != "likely_safe" and not [f for f in flags if f not in ("urgency", "click_link")]:
        flags.append("model_only")

    category = pick_category(rr.category_votes) if verdict != "likely_safe" else None
    if verdict != "likely_safe" and category == "unknown" and url_reports and any(
        r.risk == "high" for r in url_reports
    ):
        category = "phishing_link"

    v = M.VERDICTS[verdict]
    reasons = [M.t(M.FLAGS, f, lang) for f in flags]
    if verdict == "likely_safe":
        advice = list(M.SAFE_ADVICE[lang])
    else:
        advice = []
        if category and category in M.CATEGORY_ADVICE:
            advice.append(M.t(M.CATEGORY_ADVICE, category, lang))
        advice += M.GENERAL_ADVICE[lang]

    links = []
    for r in url_reports:
        d = r.to_dict()
        d["risk_label"] = M.t(M.URL_RISK_WORDS, r.risk, lang)
        d["reason_text"] = [M.t(M.URL_REASONS, x, lang) for x in r.reasons]
        links.append(d)

    result = {
        "verdict": verdict,
        "emoji": v["emoji"],
        "label": v[lang]["label"],
        "headline": v[lang]["headline"],
        "category": category,
        "category_label": M.t(M.CATEGORIES, category, lang) if category else None,
        "language_detected": detected,
        "reply_language": lang,
        "risk_score": round(risk, 3),
        "model_probability": None if p is None else round(p, 3),
        "rule_score": round(rr.score, 3),
        "red_flags": [{"id": f, "text": r} for f, r in zip(flags, reasons)],
        "links": links,
        "advice": advice,
        "disclaimer": M.DISCLAIMER[lang],
        "model_version": load_meta().get("model_version", "unknown"),
    }
    result["reply_text"] = short_reply(result)
    return result


def short_reply(result: dict, max_reasons: int = 2) -> str:
    """A chat reply of about 5 lines: verdict, type, top reasons, one action."""
    lang = result["reply_language"]
    lines = [f"{result['emoji']} {result['label']}"]
    if result["category_label"]:
        lines[0] += f" - {result['category_label']}"
    if result["verdict"] == "likely_safe":
        lines.append(result["advice"][0])
    else:
        for flag in result["red_flags"][:max_reasons]:
            lines.append("• " + flag["text"])
        lines.append("👉 " + result["advice"][0])
    lines.append("ℹ️ " + M.DISCLAIMER[lang].split(".")[0].split("।")[0] + ("।" if lang == "hi" else "."))
    return "\n".join(lines)
