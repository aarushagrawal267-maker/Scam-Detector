"""Link (URL) checks.

We NEVER open the link. Everything here looks only at the text of the link,
plus an optional lookup in Google Safe Browsing (a free list of known
dangerous sites, used only if you set an API key).

Each check returns a reason id; ``messages.py`` turns ids into plain words.
"""

from __future__ import annotations

import ipaddress
import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .text_utils import defang_url

# Brand names scammers copy, mapped to the real domains those brands use.
# If a link mentions the brand but is NOT one of these domains, it is a
# "look-alike" link, one of the strongest warning signs.
OFFICIAL_DOMAINS: dict[str, set[str]] = {
    "sbi": {"sbi.co.in", "onlinesbi.sbi", "sbi.bank.in", "sbicard.com", "yonosbi.com"},
    "hdfc": {"hdfcbank.com", "hdfc.com", "hdfclife.com", "hdfcbank.bank.in"},
    "icici": {"icicibank.com", "icicidirect.com", "iciciprulife.com", "icicibank.bank.in"},
    "axis": {"axisbank.com", "axisbank.bank.in"},
    "kotak": {"kotak.com", "kotak.bank.in"},
    "pnb": {"pnbindia.in", "pnb.bank.in"},
    "baroda": {"bankofbaroda.in", "bankofbaroda.bank.in"},
    "canara": {"canarabank.com", "canarabank.bank.in"},
    "paytm": {"paytm.com", "paytmbank.com"},
    "phonepe": {"phonepe.com"},
    "amazon": {"amazon.in", "amazon.com", "amazonpay.in"},
    "flipkart": {"flipkart.com"},
    "myntra": {"myntra.com"},
    "meesho": {"meesho.com"},
    "indiapost": {"indiapost.gov.in"},
    "bluedart": {"bluedart.com"},
    "delhivery": {"delhivery.com"},
    "dtdc": {"dtdc.in", "dtdc.com"},
    "irctc": {"irctc.co.in"},
    "aadhaar": {"uidai.gov.in"},
    "uidai": {"uidai.gov.in"},
    "incometax": {"incometax.gov.in"},
    "epfo": {"epfindia.gov.in"},
    "lic": {"licindia.in"},
    "jio": {"jio.com"},
    "airtel": {"airtel.in", "airtel.com"},
    "bsnl": {"bsnl.co.in"},
    "bses": {"bsesdelhi.com"},
    "tatapower": {"tatapower.com", "tatapower-ddl.com"},
    "mahadiscom": {"mahadiscom.in"},
    "npci": {"npci.org.in"},
    "rbi": {"rbi.org.in"},
    "whatsapp": {"whatsapp.com", "wa.me"},
    "google": {"google.com", "google.co.in", "goo.gl", "youtube.com", "youtu.be"},
}

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.ly", "cutt.ly", "rb.gy", "is.gd", "goo.gl", "ow.ly",
    "shorturl.at", "tiny.cc", "rebrand.ly", "s.id", "t.co", "bit.do", "v.gd",
    "short.gy", "shorte.st", "tinycc.com", "bl.ink", "lnkd.in", "qr.ae",
}

SUSPICIOUS_TLDS = {
    "xyz", "top", "online", "site", "club", "live", "shop", "link", "click", "vip",
    "cc", "tk", "ml", "ga", "cf", "gq", "buzz", "icu", "win", "loan", "work",
    "support", "today", "store", "pw", "rest", "fun", "monster", "cyou", "sbs",
    "cfd", "bond", "lol", "quest",
}

BAIT_WORDS = (
    "kyc", "verify", "verification", "update", "secure", "login", "signin", "reward",
    "refund", "claim", "bonus", "gift", "prize", "lucky", "free", "unlock", "block",
    "suspend", "redeliver", "customs", "pay-", "-pay", "otp", "aadhaar", "pan-",
)

# Second-level labels used under country domains, e.g. sbi.co.in, uidai.gov.in.
_SECOND_LEVEL = {"co", "gov", "org", "net", "ac", "nic", "res", "edu", "gen", "firm", "ind", "bank"}


@dataclass
class UrlReport:
    url: str
    display: str  # defanged, safe to show
    domain: str
    registered_domain: str
    risk: str = "low"  # low / medium / high
    reasons: list[str] = field(default_factory=list)
    official: bool = False
    safe_browsing: str = "not_checked"  # match / no_match / not_checked / error

    def to_dict(self) -> dict:
        return {
            "url": self.display,
            "domain": self.domain,
            "risk": self.risk,
            "reasons": self.reasons,
            "official_domain": self.official,
            "safe_browsing": self.safe_browsing,
        }


def registered_domain(host: str) -> str:
    """``secure.sbi.co.in`` -> ``sbi.co.in``; ``a.b.example.com`` -> ``example.com``."""
    parts = [p for p in host.lower().strip(".").split(".") if p]
    if len(parts) >= 3 and parts[-1] == "in" and parts[-2] in _SECOND_LEVEL:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _host_of(url: str) -> str:
    if not re.match(r"^[a-z][a-z0-9+.-]*://", url, flags=re.I):
        url = "http://" + url
    try:
        host = urlsplit(url).hostname or ""
    except ValueError:
        host = ""
    return host.lower()


def analyse_url(url: str) -> UrlReport:
    """Score one link using only its text. Never fetches the page."""
    host = _host_of(url)
    reg = registered_domain(host) if host else ""
    report = UrlReport(url=url, display=defang_url(url), domain=host, registered_domain=reg)
    reasons: list[tuple[str, str]] = []  # (reason_id, severity)

    official_set = set().union(*OFFICIAL_DOMAINS.values())
    # .gov.in, .nic.in and .bank.in can only be registered by government bodies
    # and banks, so they are much harder for scammers to get.
    if reg in official_set or host.endswith((".gov.in", ".nic.in", ".bank.in")):
        report.official = True

    lower = url.lower()
    try:
        ipaddress.ip_address(host)
        reasons.append(("ip_address", "high"))
    except ValueError:
        pass
    if "xn--" in host:
        reasons.append(("punycode", "high"))
    if "@" in lower.split("//", 1)[-1].split("/", 1)[0]:
        reasons.append(("at_sign", "high"))
    if lower.split("?")[0].endswith(".apk"):
        reasons.append(("apk_download", "high"))
    if not report.official:
        flat = re.sub(r"[^a-z0-9]", "", host)
        for brand in OFFICIAL_DOMAINS:
            if brand in flat and len(brand) >= 3:
                reasons.append(("brand_lookalike", "high"))
                break
    if reg in URL_SHORTENERS or host in URL_SHORTENERS:
        reasons.append(("shortener", "medium"))
    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    if tld in SUSPICIOUS_TLDS:
        reasons.append(("suspicious_tld", "medium"))
    if sum(c.isdigit() for c in reg) >= 3:
        reasons.append(("digits_in_domain", "medium"))
    if not report.official and any(w in host for w in BAIT_WORDS):
        reasons.append(("bait_words", "medium"))
    if host.count("-") >= 2:
        reasons.append(("many_hyphens", "medium"))
    if host.count(".") >= 4:
        reasons.append(("many_subdomains", "medium"))
    if lower.startswith("http://") and not report.official:
        reasons.append(("no_https", "low"))

    report.reasons = [r for r, _ in reasons]
    severities = {s for _, s in reasons}
    if "high" in severities:
        report.risk = "high"
    elif "medium" in severities:
        report.risk = "medium"
    else:
        report.risk = "low"
    return report


def check_safe_browsing(reports: list[UrlReport], timeout: float = 3.0) -> None:
    """Optional: ask Google Safe Browsing whether any link is on its blocklist.

    Only runs if the ``GOOGLE_SAFE_BROWSING_API_KEY`` environment variable is set.
    Only the link is sent to Google, never the rest of the message. If the call
    fails we carry on without it; we never block the user's answer on it.
    """
    key = os.environ.get("GOOGLE_SAFE_BROWSING_API_KEY")
    if not key or not reports:
        return
    try:
        import httpx

        body = {
            "client": {"clientId": "scam-message-detector", "clientVersion": "0.1.0"},
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": r.url} for r in reports],
            },
        }
        resp = httpx.post(
            "https://safebrowsing.googleapis.com/v4/threatMatches:find",
            params={"key": key},
            json=body,
            timeout=timeout,
        )
        resp.raise_for_status()
        matched = {m["threat"]["url"] for m in resp.json().get("matches", [])}
        for r in reports:
            if r.url in matched:
                r.safe_browsing = "match"
                r.risk = "high"
                if "safe_browsing_match" not in r.reasons:
                    r.reasons.insert(0, "safe_browsing_match")
            else:
                r.safe_browsing = "no_match"
    except Exception:  # network down, quota exceeded, bad key, ...
        for r in reports:
            r.safe_browsing = "error"
