"""Small text helpers: cleaning, language detection and anonymisation.

Why these exist
---------------
* Scam messages arrive in English, Hindi (Devanagari script) and Hinglish
  (Hindi words typed in English letters, e.g. "aapka account band ho jayega").
  We need to know which one we're looking at so we can reply in a language the
  user understands, and so we can measure accuracy separately per language.
* Before we store anything for research, personal details (phone numbers,
  e-mail addresses, account numbers) must be removed.
"""

from __future__ import annotations

import re
import unicodedata

# Devanagari Unicode block: U+0900 to U+097F
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_LATIN = re.compile(r"[A-Za-z]")

# Common Hindi words written in Roman letters. If a Latin-script message uses
# several of these, it is probably Hinglish. The list is deliberately small and
# made of words that are rare in English.
HINGLISH_MARKERS = {
    "aap", "aapka", "aapke", "aapki", "apka", "apke", "apki", "hai", "hain", "ho",
    "hoga", "hogi", "gaya", "gayi", "kare", "karein", "karen", "karo", "kijiye",
    "jaldi", "turant", "abhi", "nahi", "nahin", "mat", "kya", "kyu", "kyun",
    "mera", "meri", "mere", "tera", "tumhara", "bhai", "beta", "paisa", "paise",
    "rupaye", "rupay", "jayega", "jayegi", "jaega", "karna", "karne", "wala",
    "wali", "lekin", "aur", "ke", "ki", "ka", "ko", "se", "par", "pe", "mein",
    "liye", "dijiye", "bhejo", "bheje", "bhejiye", "batao", "bataye", "band",
    "khata", "inaam", "jeeta", "jeete", "sampark", "kripya", "krupya", "dhanyavad",
    "shukriya", "naya", "purana", "ghar", "baithe", "kamaye", "kamao", "lijiye",
}

_URL_RE = re.compile(
    r"""(?xi)
    \b(
        (?:https?://|www\.)[^\s<>"']+                # http://..., https://..., www....
        |
        (?:[a-z0-9-]+\.)+(?:com|in|net|org|info|xyz|top|online|site|club|live|
            shop|link|click|co|me|io|app|vip|cc|tk|ml|ga|cf|gq|buzz|icu|win|
            loan|work|support|today|store|pw|ly|gl|gd|to|sh)
        (?:/[^\s<>"']*)?                              # bare domains like sbi-kyc.xyz/abc
    )
    """
)

_PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
_ANY_LONG_NUMBER_RE = re.compile(r"(?<!\d)\d[\d\s-]{8,}\d(?!\d)")
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def normalise(text: str) -> str:
    """Return a cleaned-up copy of ``text`` for analysis.

    * Unicode NFKC normalisation turns look-alike characters (full-width
      letters, some fancy fonts scammers use) into their plain forms.
    * Zero-width characters, sometimes inserted to dodge filters, are removed.
    * Whitespace is collapsed.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[​-‏⁠﻿]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def detect_language(text: str) -> str:
    """Guess the language style of a message.

    Returns one of ``"hi"`` (Devanagari Hindi), ``"hinglish"`` (Hindi in Roman
    letters, often mixed with English) or ``"en"`` (English).

    This is a simple rule, not a trained model, so it can be wrong on very short
    messages. It is good enough to pick a reply language and to group results.
    """
    text = text or ""
    deva = len(_DEVANAGARI.findall(text))
    latin = len(_LATIN.findall(text))
    if deva and deva >= 0.3 * (deva + latin):
        return "hi"
    words = re.findall(r"[a-z]+", text.lower())
    if not words:
        return "en"
    hits = sum(1 for w in words if w in HINGLISH_MARKERS)
    # Two marker words, or >=15% of the words, is a reasonable Hinglish signal.
    if hits >= 2 and hits / len(words) >= 0.08:
        return "hinglish"
    return "en"


def find_urls(text: str) -> list[str]:
    """Return every link-looking string in the message, in order, without duplicates."""
    seen: list[str] = []
    for match in _URL_RE.finditer(text or ""):
        url = match.group(1).rstrip(".,;:!?)]}'\"")
        if url and url not in seen:
            seen.append(url)
    return seen


def find_phone_numbers(text: str) -> list[str]:
    return [m.group(0) for m in _PHONE_RE.finditer(text or "")]


def defang_url(url: str) -> str:
    """Make a link unclickable for display, e.g. ``https://x.com`` -> ``hxxps://x[.]com``.

    Security researchers do this so nobody opens a dangerous link by accident.
    """
    url = re.sub(r"^http", "hxxp", url, flags=re.I)
    return url.replace(".", "[.]")


def anonymise(text: str) -> str:
    """Remove personal details before a message is ever saved for research.

    Phone numbers, e-mail addresses and long digit strings (account, card,
    Aadhaar numbers) are replaced with placeholders. Links are kept but
    defanged, because the link itself is evidence about the scam.

    Names cannot be removed reliably by a simple rule, so research data must
    still be checked by a human before it is used.
    """
    text = _EMAIL_RE.sub("[EMAIL]", text or "")
    for url in find_urls(text):
        text = text.replace(url, defang_url(url))
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _ANY_LONG_NUMBER_RE.sub("[NUMBER]", text)
    return text
