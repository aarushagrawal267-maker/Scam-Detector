"""Rule-based red-flag detection.

The machine-learning model gives a probability, but it can't explain itself in
words a grandparent understands. These hand-written rules look for the tricks
scammers use (urgency, asking for an OTP, prizes, threats...) in English,
Hinglish and Hindi. Each rule that fires becomes a plain-language reason in the
reply, and also nudges the risk score up.

Each rule has:
  * ``id``        - a short name, translated in ``messages.py``
  * ``weight``    - how strongly it suggests a scam (0 to 1)
  * ``categories``- which scam types it points to
  * ``patterns``  - regular expressions, matched on lower-cased text

How rules are combined ("noisy-OR"):
    rule_score = 1 - (1 - w1) * (1 - w2) * ...
Two weak signals together give a stronger score than either alone, but the
score never goes above 1.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Words that, just before "share", mean "do NOT share". Genuine OTP messages
# say "Do not share this OTP with anyone"; that is a safe sign, not a red flag.
_NEGATION = re.compile(
    r"(do not|don't|dont|never|not to|na kare|na karein|mat|naa|kabhi|न करें|ना करें|मत|कभी)\W*(\w+\W+){0,3}$"
)


@dataclass(frozen=True)
class Rule:
    id: str
    weight: float
    categories: tuple[str, ...]
    patterns: tuple[str, ...]
    negatable: bool = False  # True: ignore a match preceded by "do not" etc.


RULES: tuple[Rule, ...] = (
    Rule(
        "asks_for_otp",
        0.65,
        ("otp_theft",),
        (
            r"\b(share|send|tell|give|provide|forward|reply with|enter|batao|bataye|batayein|bhejo|bheje|bhejiye|de do|dijiye|btao)\b[^.!?\n]{0,40}\b(otp|pin|cvv|password|passcode|verification code|m-?pin)\b",
            r"\b(otp|pin|cvv|password|verification code)\b[^.!?\n]{0,30}\b(share|send|batao|bataye|bhejo|bheje|bhejiye|de do|dijiye|reply|forward)\b",
            r"(ओटीपी|पिन|पासवर्ड|सीवीवी)[^।.!?\n]{0,30}(बताएं|बताइए|बताओ|भेजें|भेजो|शेयर|दें|दीजिए)",
        ),
        negatable=True,
    ),
    Rule(
        "pin_to_receive_money",
        0.7,
        ("otp_theft",),
        (
            r"(enter|daale|dalein|daalo)[^.!?\n]{0,30}(upi )?pin[^.!?\n]{0,40}(receive|get|credit|paane|milega)",
            r"(scan|approve|accept)[^.!?\n]{0,30}(qr|request)[^.!?\n]{0,40}(receive|get|refund|cashback|paane)",
            r"(पैसे|राशि|रकम)[^।\n]{0,30}(पाने|प्राप्त)[^।\n]{0,30}(पिन|pin)",
        ),
    ),
    Rule(
        "asks_for_bank_details",
        0.5,
        ("fake_bank_kyc",),
        (
            r"\b(share|send|update|provide|enter|confirm|batao|bhejo)\b[^.!?\n]{0,40}\b(card number|account number|bank details|net ?banking|atm pin|debit card|credit card details|aadhaar number|pan number|date of birth)\b",
            r"(खाता संख्या|कार्ड नंबर|बैंक विवरण|आधार नंबर)[^।\n]{0,30}(भेजें|बताएं|अपडेट)",
        ),
        negatable=True,
    ),
    Rule(
        "kyc_update",
        0.25,  # weak alone: genuine banks also send KYC reminders. Strong with a link/threat.
        ("fake_bank_kyc",),
        (
            r"\bkyc\b",
            r"\b(pan|aadhaa?r)\b[^.!?\n]{0,25}\b(link|update|verify|verification|expired?|band|block)",
            r"(केवाईसी|के\.?वाई\.?सी)",
            r"(पैन|आधार)[^।\n]{0,25}(लिंक|अपडेट|सत्यापन)",
        ),
    ),
    Rule(
        "account_threat",
        0.4,
        ("fake_bank_kyc",),
        (
            r"\b(account|a/c|acct|card|sim|number|wallet|khata|connection)\b[^.!?\n]{0,40}\b(blocked|block|suspended|suspend|deactivated|deactivate|closed|frozen|freeze|terminated|disabled|band|bandh)\b",
            r"\b(will be|has been|is|ho jayega|ho gaya|kar diya)\b[^.!?\n]{0,15}\b(blocked|suspended|deactivated|frozen|band)\b",
            r"(खाता|कार्ड|सिम|कनेक्शन)[^।\n]{0,30}(बंद|ब्लॉक|निलंबित)",
        ),
    ),
    Rule(
        "urgency",
        0.25,
        (),
        (
            r"\b(urgent|urgently|immediately|immediate|asap|right now|act now|within \d+ ?(hours?|hrs?|minutes?|mins?)|today only|last chance|last date|expires? (today|soon|tonight)|final (notice|warning|reminder)|tonight)\b",
            r"\b(turant|jaldi|abhi|fauran|aaj hi|aaj raat)\b",
            r"(तुरंत|जल्दी|अभी|फौरन|आज ही|आज रात|अंतिम चेतावनी)",
        ),
    ),
    Rule(
        "prize_or_lottery",
        0.5,
        ("lottery_prize",),
        (
            r"\b(you have won|you've won|you won|winner|won (a|an|rs|inr|₹)|lottery|lucky draw|jackpot|kbc|kaun banega crorepati|prize money|claim (your )?(prize|reward|gift)|selected for (a )?(reward|prize|gift)|cash ?prize|bumper)\b",
            r"\b(inaam|jeeta|jeete|jeeti|lucky winner)\b",
            r"(इनाम|लॉटरी|जीत|विजेता|पुरस्कार|केबीसी)",
        ),
    ),
    Rule(
        "upfront_fee",
        0.45,
        (),
        (
            r"\b(pay|deposit|transfer|send)\b[^.!?\n]{0,30}\b(fee|fees|charge|charges|tax|gst|deposit|amount)\b[^.!?\n]{0,30}\b(to (receive|claim|release|get|activate|process)|for (registration|processing|delivery|release|clearance|activation))",
            r"\b(registration|processing|clearance|customs|delivery|redelivery|activation|security|verification|file) (fee|fees|charge|charges|duty)\b",
            r"\b(fees?|charge|shulk)\b[^.!?\n]{0,20}\b(bharo|bhariye|bharein|jama karo|jama karein|pay karo|pay karein)\b",
            r"(शुल्क|फीस|चार्ज)[^।\n]{0,25}(भरें|जमा करें|भेजें|भुगतान)",
        ),
    ),
    Rule(
        "remote_access_app",
        0.6,
        ("remote_access",),
        (
            r"\b(anydesk|any desk|teamviewer|team viewer|quick ?support|rustdesk|airdroid|screen ?share|screen sharing)\b",
            r"\b(download|install)\b[^.!?\n]{0,30}\b(app|apk|application)\b[^.!?\n]{0,40}\b(from|via|using|at|on) (this |the )?(link|url)",
            r"\.apk\b",
        ),
    ),
    Rule(
        "authority_threat",
        0.55,
        ("government_impersonation",),
        (
            r"\b(cbi|police|crime branch|cyber cell|narcotics|ncb|enforcement directorate|customs officer|trai|income tax department|court|magistrate|interpol|rbi officer|fedex)\b[^.!?\n]{0,80}\b(arrest|warrant|case|fir|illegal|drugs|seized|legal action|penalty|summon|investigation|money laundering)\b",
            r"\b(digital arrest|arrest warrant|money laundering|drugs (were )?found|illegal parcel|legal action (will be|against))\b",
            r"(डिजिटल अरेस्ट|गिरफ्तारी|वारंट|पुलिस|सीबीआई|कानूनी कार्रवाई|मनी लॉन्ड्रिंग)",
        ),
    ),
    Rule(
        "secrecy",
        0.45,
        (),
        (
            r"\b(don't|do not|dont) (tell|inform|share this with) (anyone|anybody|your family|family|bank)\b",
            r"\b(keep (this|it) (secret|confidential)|confidential matter)\b",
            r"\b(kisi ko (bhi )?(mat|na) (batana|batayein|bataye|bolna))\b",
            r"(किसी को (भी )?(न|मत) (बताएं|बताना|बताइए))",
        ),
    ),
    Rule(
        "new_number_family",
        0.5,
        ("family_impersonation",),
        (
            r"\b(hi|hello|hey)?\s*(mum|mom|mummy|mumma|dad|daddy|papa|maa|beta|bhaiya|didi|uncle|aunty)\b[^.!?\n]{0,60}\b(new number|my number|lost my phone|phone (broke|broken|lost|stolen|kharab)|naya number|mera number)\b",
            r"\b(this is my new number|my new number|mera naya number|naya number hai|new no\.?)\b",
            r"(मेरा नया नंबर|नया नंबर है|फोन खो गया|फोन खराब)",
        ),
    ),
    Rule(
        "send_money_request",
        0.4,
        (),
        (
            r"\b(send|transfer|pay|gpay|google pay|phonepe|paytm)\b[^.!?\n]{0,25}\b(me|money|rs\.?|inr|₹|amount|urgently)\b[^.!?\n]{0,40}\b(urgent|urgently|emergency|hospital|accident|stuck|today|now|asap|jaldi|abhi)\b",
            r"\b(paise|paisa|rupaye|money)\b[^.!?\n]{0,20}\b(bhejo|bhej do|bhejiye|transfer karo|chahiye)\b",
            r"(पैसे|रुपये)[^।\n]{0,20}(भेजो|भेज दो|भेजिए|चाहिए|ट्रांसफर)",
        ),
    ),
    Rule(
        "job_offer",
        0.45,
        ("job_offer",),
        (
            r"\b(work from home|part[- ]?time (job|work)|home based (job|work)|data entry job|online job|daily (income|salary|payment|earning))\b",
            r"\b(earn|income|salary|kamaye|kamao)\b[^.!?\n]{0,30}(rs\.?|inr|₹)?\s?\d[\d,]*\s*(\+|-)?\s*(per|a|/|daily|every|roz|pratidin)\s*(day|daily|hour|task|din)?",
            r"\b(like|rate|review|subscribe)\b[^.!?\n]{0,25}\b(videos?|hotels?|products?|channels?|posts?)\b[^.!?\n]{0,40}\b(earn|paid|income|commission|rs|₹)",
            r"\b(ghar baithe|ghar se kaam)\b",
            r"(घर बैठे|पार्ट टाइम|रोज़? कमाएं|रोजाना कमाई)",
        ),
    ),
    Rule(
        "investment_promise",
        0.5,
        ("investment_crypto",),
        (
            r"\b(guaranteed (returns?|profit|income)|double your money|money double|paisa double|risk[- ]free (returns?|profit|investment)|\d{2,3}\s?% (returns?|profit) (daily|weekly|monthly|guaranteed)|assured returns?)\b",
            r"\b(crypto|bitcoin|btc|usdt|forex|trading (tips|group|signals)|stock (tips|market tips)|ipo allotment|vip (group|trading))\b",
            r"(पैसा डबल|गारंटीड रिटर्न|निश्चित मुनाफा|क्रिप्टो|बिटकॉइन)",
        ),
    ),
    Rule(
        "parcel_problem",
        0.4,
        ("delivery_fee",),
        (
            r"\b(parcel|package|shipment|courier|consignment|order|delivery)\b[^.!?\n]{0,60}\b(on hold|held|pending|failed|could not be delivered|undeliverable|incomplete address|address (is )?incomplete|returned|stuck|seized|customs)\b",
            r"\b(redeliver|re-deliver|reschedule (your )?delivery|update (your )?(delivery )?address)\b",
            r"(पार्सल|कूरियर)[^।\n]{0,40}(रुका|अटका|रोका|पता अधूरा|कस्टम)",
        ),
    ),
    Rule(
        "bill_disconnection",
        0.4,
        ("electricity_bill",),
        (
            r"\b(electricity|power|bijli|light)\b[^.!?\n]{0,60}\b(disconnect|disconnected|disconnection|cut|kat|katega|kaat|band)\b",
            r"\b(bill)\b[^.!?\n]{0,40}\b(not (been )?updated|not paid|unpaid)\b[^.!?\n]{0,60}\b(tonight|today|9:?30|10:?30|call)\b",
            r"(बिजली)[^।\n]{0,40}(काट|कट|बंद)",
        ),
    ),
    Rule(
        "loan_offer",
        0.3,
        ("loan_offer",),
        (
            r"\b(pre[- ]?approved|instant|guaranteed|without (cibil|documents?)|no (cibil|documents?)|low cibil)\b[^.!?\n]{0,30}\b(loan|credit)\b",
            r"\b(loan)\b[^.!?\n]{0,30}\b(approved|sanctioned)\b[^.!?\n]{0,60}\b(click|link|apply|pay|fee)\b",
            r"(तुरंत लोन|बिना दस्तावेज़? लोन|लोन मंजूर)",
        ),
    ),
    Rule(
        "romance_money",
        0.4,
        ("romance",),
        (
            r"\b(my love|darling|sweetheart|honey|dear love|jaan|baby)\b[^\n]{0,120}\b(gift|parcel|customs|send|money|transfer|help me|hospital|ticket|visa)\b",
            r"\b(gift|parcel|package)\b[^.!?\n]{0,40}\b(for you)\b[^.!?\n]{0,60}\b(customs|clearance|fee|charge)\b",
        ),
    ),
    Rule(
        "refund_or_cashback",
        0.3,
        ("fake_bank_kyc",),
        (
            r"\b(refund|cashback|reward points?|redeem)\b[^.!?\n]{0,60}\b(click|link|claim|expire|expiring|verify|update|http|www)\b",
            r"(रिफंड|कैशबैक|रिवॉर्ड)[^।\n]{0,40}(क्लिक|लिंक|क्लेम)",
        ),
    ),
    Rule(
        "call_this_number",
        0.2,
        (),
        (
            r"\b(call|contact|whatsapp|dial|ring|sampark karein|sampark kare|call karein|call kare|call karo)\b[^.!?\n]{0,25}(\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}",
            r"(संपर्क करें|कॉल करें)[^।\n]{0,25}\d{10}",
        ),
    ),
    Rule(
        "click_link",
        0.15,
        (),
        (
            r"\b(click|tap|open|visit|follow)\b[^.!?\n]{0,30}\b(link|here|below|url)\b",
            r"\b(link par|link pe|link par click)\b",
            r"(लिंक पर क्लिक|लिंक खोलें)",
        ),
    ),
)

_COMPILED = [(rule, [re.compile(p, re.IGNORECASE) for p in rule.patterns]) for rule in RULES]

# "Safe signals": phrases genuine banks and companies use that point the reader
# to an OFFICIAL channel instead of a link or a stranger's number. They halve the
# rule score, but never when the message also has a dangerous link or asks for an
# OTP/PIN (scammers can copy these phrases, so they only ever soften rules,
# never the ML model). Added after error analysis on the validation set showed
# genuine KYC reminders were being flagged.
SAFE_SIGNALS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b(visit|visiting|go to|going to|contact|contacting)\b[^.!?\n]{0,25}\b(your )?(nearest|nearby|home|base) branch\b",
        r"\bofficial (app|website|site|mobile app)\b",
        r"\b(successfully|has been) (updated|completed|processed|approved|verified)\b",
        r"\bno (further )?action (is )?(needed|required)\b",
        r"\bignore if (already )?(paid|done|completed)\b",
        r"\b(do not|don't|never) (share|click)\b",
        r"(नजदीकी|निकटतम) (शाखा|branch)",
        r"(आधिकारिक|official) (ऐप|app|वेबसाइट)",
    )
)
SAFE_SIGNAL_FACTOR = 0.5
_NEVER_SOFTEN = {"asks_for_otp", "pin_to_receive_money", "remote_access_app", "authority_threat", "risky_link"}

# Link-risk reasons from urls.py also count as red flags, with these weights.
URL_FLAG_WEIGHTS = {"high": 0.55, "medium": 0.3, "low": 0.05}


@dataclass
class RuleResult:
    flags: list[str]
    score: float
    category_votes: dict[str, float]
    safe_signals: list[str] = field(default_factory=list)


def _negated(text: str, start: int) -> bool:
    window = text[max(0, start - 30) : start]
    return bool(_NEGATION.search(window))


def find_red_flags(text: str) -> RuleResult:
    """Run every rule on ``text`` and return the flags that fired."""
    lower = text.lower()
    flags: list[str] = []
    votes: dict[str, float] = {}
    keep = 1.0
    for rule, patterns in _COMPILED:
        hit = False
        for pat in patterns:
            for m in pat.finditer(lower):
                if rule.negatable and _negated(lower, m.start()):
                    continue
                hit = True
                break
            if hit:
                break
        if hit:
            flags.append(rule.id)
            keep *= 1.0 - rule.weight
            for cat in rule.categories:
                votes[cat] = votes.get(cat, 0.0) + rule.weight
    safe = [p.pattern for p in SAFE_SIGNALS if p.search(lower)]
    return RuleResult(flags=flags, score=1.0 - keep, category_votes=votes, safe_signals=safe)


def combine_with_url_risk(result: RuleResult, url_risks: list[str]) -> RuleResult:
    """Add link risk ('high'/'medium'/'low') into the noisy-OR rule score."""
    keep = 1.0 - result.score
    flags = list(result.flags)
    worst = None
    for level in ("high", "medium"):
        if level in url_risks:
            worst = level
            break
    if worst:
        keep *= 1.0 - URL_FLAG_WEIGHTS[worst]
        flags.append("risky_link" if worst == "high" else "unusual_link")
        if worst == "high":
            result.category_votes["phishing_link"] = result.category_votes.get("phishing_link", 0) + 0.3
    score = 1.0 - keep
    # Soften the rule score if the message points to official channels, unless
    # it also contains one of the never-soften danger signs.
    if result.safe_signals and not (set(flags) & _NEVER_SOFTEN):
        score *= SAFE_SIGNAL_FACTOR
    return RuleResult(flags=flags, score=score, category_votes=result.category_votes,
                      safe_signals=result.safe_signals)


# Category chosen when several rules point different ways: highest vote wins,
# ties broken by this priority (more specific / more dangerous first).
CATEGORY_PRIORITY = (
    "government_impersonation",
    "otp_theft",
    "remote_access",
    "family_impersonation",
    "fake_bank_kyc",
    "electricity_bill",
    "delivery_fee",
    "lottery_prize",
    "investment_crypto",
    "job_offer",
    "loan_offer",
    "romance",
    "phishing_link",
)


def pick_category(votes: dict[str, float]) -> str:
    if not votes:
        return "unknown"
    best = max(votes.values())
    for cat in CATEGORY_PRIORITY:
        if votes.get(cat) == best:
            return cat
    return max(votes, key=votes.get)
