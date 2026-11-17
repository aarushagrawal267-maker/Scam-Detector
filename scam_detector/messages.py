"""Everything the user reads, in English ("en") and Hindi ("hi").

Design rules (from the UX plan for elderly users):
  * short sentences, everyday words, no jargon;
  * verdict = emoji + WORD (never colour alone, for colour-blind users);
  * a green result never says "safe", only "likely safe, but not guaranteed";
  * always point to official help: 1930, cybercrime.gov.in, Sanchar Saathi (Chakshu).
"""

from __future__ import annotations

LANGS = ("en", "hi")

VERDICTS = {
    "scam": {
        "emoji": "🔴",
        "en": {"label": "SCAM", "headline": "This looks like a SCAM."},
        "hi": {"label": "धोखा (स्कैम)", "headline": "यह मैसेज धोखा (स्कैम) लगता है।"},
    },
    "suspicious": {
        "emoji": "🟡",
        "en": {"label": "SUSPICIOUS", "headline": "Be careful. This message is SUSPICIOUS."},
        "hi": {"label": "संदिग्ध", "headline": "सावधान रहें। यह मैसेज संदिग्ध है।"},
    },
    "likely_safe": {
        "emoji": "🟢",
        "en": {
            "label": "LIKELY SAFE",
            "headline": "No common scam signs found. This is NOT a guarantee.",
        },
        "hi": {
            "label": "शायद सुरक्षित",
            "headline": "धोखे के आम निशान नहीं मिले। पर यह पक्का नहीं है।",
        },
    },
}

CATEGORIES = {
    "fake_bank_kyc": {"en": "Fake bank / KYC alert", "hi": "नकली बैंक / KYC मैसेज"},
    "otp_theft": {"en": "OTP / PIN theft", "hi": "OTP / PIN चोरी"},
    "lottery_prize": {"en": "Fake lottery or prize", "hi": "नकली लॉटरी या इनाम"},
    "job_offer": {"en": "Fake job offer", "hi": "नकली नौकरी"},
    "family_impersonation": {"en": "Someone pretending to be family", "hi": "परिवार का सदस्य बनकर धोखा"},
    "delivery_fee": {"en": "Fake parcel / delivery fee", "hi": "नकली पार्सल / डिलीवरी फीस"},
    "investment_crypto": {"en": "Investment or crypto scam", "hi": "निवेश या क्रिप्टो धोखा"},
    "romance": {"en": "Romance scam", "hi": "दोस्ती या प्यार के नाम पर धोखा"},
    "government_impersonation": {"en": "Fake police / 'digital arrest'", "hi": "नकली पुलिस / 'डिजिटल अरेस्ट'"},
    "electricity_bill": {"en": "Fake electricity bill", "hi": "नकली बिजली बिल"},
    "loan_offer": {"en": "Fake loan offer", "hi": "नकली लोन"},
    "remote_access": {"en": "Screen-sharing app trick", "hi": "स्क्रीन शेयर / रिमोट ऐप धोखा"},
    "phishing_link": {"en": "Dangerous link (phishing)", "hi": "खतरनाक लिंक (फ़िशिंग)"},
    "unknown": {"en": "Type unclear", "hi": "प्रकार साफ़ नहीं"},
}

FLAGS = {
    "asks_for_otp": {
        "en": "It asks for your OTP, PIN or password. No real bank or company ever asks for these.",
        "hi": "यह आपका OTP, PIN या पासवर्ड मांग रहा है। कोई भी असली बैंक या कंपनी यह कभी नहीं मांगती।",
    },
    "pin_to_receive_money": {
        "en": "It says to enter your UPI PIN or scan a code to RECEIVE money. You never need a PIN to receive money.",
        "hi": "यह पैसे पाने के लिए UPI PIN डालने या QR स्कैन करने को कहता है। पैसे पाने के लिए PIN की कभी ज़रूरत नहीं होती।",
    },
    "asks_for_bank_details": {
        "en": "It asks for your bank, card or Aadhaar details.",
        "hi": "यह आपके बैंक, कार्ड या आधार की जानकारी मांग रहा है।",
    },
    "kyc_update": {
        "en": "It asks you to update KYC, PAN or Aadhaar from a message. Banks do not do this through SMS links.",
        "hi": "यह मैसेज से KYC, PAN या आधार अपडेट करने को कहता है। बैंक ऐसा SMS लिंक से नहीं करवाते।",
    },
    "account_threat": {
        "en": "It threatens that your account, card or SIM will be blocked.",
        "hi": "यह डराता है कि आपका खाता, कार्ड या सिम बंद हो जाएगा।",
    },
    "urgency": {
        "en": "It rushes you to act fast, so you don't stop to think.",
        "hi": "यह जल्दी करने का दबाव डालता है, ताकि आप सोच न सकें।",
    },
    "prize_or_lottery": {
        "en": "It says you won a prize or lottery you never entered.",
        "hi": "यह कहता है कि आपने इनाम या लॉटरी जीती है, जिसमें आपने हिस्सा ही नहीं लिया।",
    },
    "upfront_fee": {
        "en": "It asks you to pay a fee first to get money, a parcel or a job.",
        "hi": "यह कहता है कि पैसा, पार्सल या नौकरी पाने के लिए पहले फीस भरें।",
    },
    "remote_access_app": {
        "en": "It asks you to install an app (like AnyDesk) or an .apk file. A stranger could then control your phone.",
        "hi": "यह AnyDesk जैसा ऐप या .apk फ़ाइल डाउनलोड करने को कहता है। इससे कोई अजनबी आपका फ़ोन चला सकता है।",
    },
    "authority_threat": {
        "en": "It pretends to be police, CBI, customs or a court and threatens arrest. Real police never arrest anyone on a phone or video call.",
        "hi": "यह पुलिस, CBI, कस्टम या कोर्ट बनकर गिरफ्तारी की धमकी देता है। असली पुलिस फ़ोन या वीडियो कॉल पर गिरफ्तार नहीं करती।",
    },
    "secrecy": {
        "en": "It tells you to keep this secret. Scammers don't want your family or bank to warn you.",
        "hi": "यह बात छुपाने को कहता है। ठग नहीं चाहते कि आपका परिवार या बैंक आपको सावधान करे।",
    },
    "new_number_family": {
        "en": "Someone says they are family, writing from a new number.",
        "hi": "कोई नए नंबर से परिवार का सदस्य होने का दावा कर रहा है।",
    },
    "send_money_request": {
        "en": "It asks you to send money urgently.",
        "hi": "यह तुरंत पैसे भेजने को कहता है।",
    },
    "job_offer": {
        "en": "It promises easy money for simple online work.",
        "hi": "यह आसान ऑनलाइन काम के लिए ज़्यादा पैसे का वादा करता है।",
    },
    "investment_promise": {
        "en": "It promises guaranteed or very high profit. Real investments never guarantee profit.",
        "hi": "यह पक्के या बहुत ज़्यादा मुनाफ़े का वादा करता है। असली निवेश में मुनाफ़े की गारंटी नहीं होती।",
    },
    "parcel_problem": {
        "en": "It says your parcel is stuck or needs action.",
        "hi": "यह कहता है कि आपका पार्सल अटका है या कुछ करना होगा।",
    },
    "bill_disconnection": {
        "en": "It threatens to cut your electricity soon.",
        "hi": "यह जल्द बिजली काटने की धमकी देता है।",
    },
    "loan_offer": {
        "en": "It offers an easy loan with no checks.",
        "hi": "यह बिना जांच के आसान लोन देने का वादा करता है।",
    },
    "romance_money": {
        "en": "Someone you know only online is asking for money or a fee.",
        "hi": "जिसे आप सिर्फ़ ऑनलाइन जानते हैं, वह पैसे या फीस मांग रहा है।",
    },
    "refund_or_cashback": {
        "en": "It offers a refund or reward through a link.",
        "hi": "यह लिंक के ज़रिए रिफंड या इनाम देने की बात करता है।",
    },
    "call_this_number": {
        "en": "It asks you to call or WhatsApp a personal mobile number.",
        "hi": "यह किसी निजी मोबाइल नंबर पर कॉल या WhatsApp करने को कहता है।",
    },
    "click_link": {
        "en": "It pushes you to click a link.",
        "hi": "यह लिंक पर क्लिक करने का दबाव डालता है।",
    },
    "risky_link": {
        "en": "The link in it looks dangerous.",
        "hi": "इसमें दिया लिंक खतरनाक लगता है।",
    },
    "unusual_link": {
        "en": "The link in it looks unusual.",
        "hi": "इसमें दिया लिंक अजीब लगता है।",
    },
    "model_only": {
        "en": "Our AI model found this message very similar to known scam messages.",
        "hi": "हमारे AI मॉडल को यह मैसेज जाने-पहचाने धोखे वाले मैसेज जैसा लगा।",
    },
}

URL_REASONS = {
    "safe_browsing_match": {"en": "is on Google's list of dangerous websites", "hi": "Google की खतरनाक वेबसाइटों की सूची में है"},
    "ip_address": {"en": "uses numbers instead of a website name", "hi": "वेबसाइट के नाम की जगह नंबर हैं"},
    "punycode": {"en": "uses look-alike letters to copy a real website", "hi": "असली वेबसाइट जैसे दिखने वाले नकली अक्षर हैं"},
    "at_sign": {"en": "uses an '@' trick to hide the real website", "hi": "'@' की चाल से असली वेबसाइट छुपाता है"},
    "apk_download": {"en": "downloads an app file (.apk)", "hi": "ऐप फ़ाइल (.apk) डाउनलोड करवाता है"},
    "brand_lookalike": {"en": "copies a well-known name but is NOT that company's real website", "hi": "किसी बड़ी कंपनी का नाम इस्तेमाल करता है, पर उसकी असली वेबसाइट नहीं है"},
    "shortener": {"en": "is a short link that hides where it really goes", "hi": "छोटा लिंक है जो असली पता छुपाता है"},
    "suspicious_tld": {"en": "has an ending (like .xyz or .top) often used by scammers", "hi": "इसका अंत (.xyz या .top जैसा) अक्सर ठग इस्तेमाल करते हैं"},
    "digits_in_domain": {"en": "has random numbers in the website name", "hi": "वेबसाइट के नाम में बेतरतीब नंबर हैं"},
    "bait_words": {"en": "uses words like 'kyc', 'verify' or 'reward' in the address", "hi": "पते में 'kyc', 'verify' या 'reward' जैसे शब्द हैं"},
    "many_hyphens": {"en": "has many dashes in its name", "hi": "नाम में कई डैश (-) हैं"},
    "many_subdomains": {"en": "is unusually long with many parts", "hi": "बहुत लंबा और कई हिस्सों वाला है"},
    "no_https": {"en": "is not a secure (https) link", "hi": "सुरक्षित (https) लिंक नहीं है"},
}

URL_RISK_WORDS = {
    "high": {"en": "Dangerous", "hi": "खतरनाक"},
    "medium": {"en": "Unusual", "hi": "अजीब"},
    "low": {"en": "No obvious problem (still don't trust it blindly)", "hi": "कोई साफ़ खतरा नहीं (फिर भी आंख बंद कर भरोसा न करें)"},
}

GENERAL_ADVICE = {
    "en": [
        "Do not click any link or call any number in this message.",
        "Never share your OTP, PIN, password or card details with anyone.",
        "To check, call the number printed on your bank card or passbook, or on the company's official website.",
        "Lost money? Call 1930 at once, or report at cybercrime.gov.in.",
        "Report the fake message at sancharsaathi.gov.in (Chakshu), then block the sender.",
    ],
    "hi": [
        "इस मैसेज के किसी लिंक पर क्लिक न करें और किसी नंबर पर कॉल न करें।",
        "अपना OTP, PIN, पासवर्ड या कार्ड की जानकारी किसी को न बताएं।",
        "जांच के लिए अपने बैंक कार्ड, पासबुक या कंपनी की असली वेबसाइट पर लिखा नंबर ही इस्तेमाल करें।",
        "पैसे चले गए? तुरंत 1930 पर कॉल करें या cybercrime.gov.in पर शिकायत करें।",
        "नकली मैसेज की शिकायत sancharsaathi.gov.in (चक्षु) पर करें, फिर भेजने वाले को ब्लॉक करें।",
    ],
}

CATEGORY_ADVICE = {
    "family_impersonation": {
        "en": "Call the person on their OLD number, or ask something only they would know.",
        "hi": "उस व्यक्ति को उनके पुराने नंबर पर फ़ोन करें, या कोई ऐसी बात पूछें जो सिर्फ़ वही जानते हों।",
    },
    "government_impersonation": {
        "en": "Hang up. There is no such thing as a 'digital arrest'. Tell a family member right away.",
        "hi": "फ़ोन काट दें। 'डिजिटल अरेस्ट' जैसी कोई चीज़ नहीं होती। तुरंत परिवार में किसी को बताएं।",
    },
    "otp_theft": {
        "en": "Your OTP is the key to your bank account. Only you should type it, in your bank's own app.",
        "hi": "आपका OTP आपके बैंक खाते की चाबी है। इसे सिर्फ़ आप, अपने बैंक के असली ऐप में डालें।",
    },
    "remote_access": {
        "en": "Uninstall any app a stranger asked you to install, then call your bank's official number.",
        "hi": "किसी अजनबी के कहने पर डाला गया ऐप हटा दें, फिर बैंक के असली नंबर पर फ़ोन करें।",
    },
    "job_offer": {"en": "Real jobs never ask you to pay to start working.", "hi": "असली नौकरी में काम शुरू करने के लिए पैसे नहीं देने पड़ते।"},
    "investment_crypto": {
        "en": "Never invest through a stranger's WhatsApp or Telegram group.",
        "hi": "किसी अजनबी के WhatsApp या Telegram ग्रुप के ज़रिए कभी निवेश न करें।",
    },
    "delivery_fee": {
        "en": "Track parcels only in the courier's official app or website that you open yourself.",
        "hi": "पार्सल सिर्फ़ कूरियर के असली ऐप या वेबसाइट पर देखें, जिसे आप खुद खोलें।",
    },
    "electricity_bill": {
        "en": "Check your bill in your electricity company's official app, or at its office.",
        "hi": "अपना बिल बिजली कंपनी के असली ऐप या दफ़्तर में ही जांचें।",
    },
    "lottery_prize": {
        "en": "You cannot win a lottery you never entered. Never pay to receive a prize.",
        "hi": "जिस लॉटरी में आपने हिस्सा नहीं लिया, उसे आप जीत नहीं सकते। इनाम पाने के लिए कभी पैसे न भरें।",
    },
    "loan_offer": {
        "en": "Take loans only from your bank branch or a lender you have checked.",
        "hi": "लोन सिर्फ़ अपने बैंक की शाखा या जांचे हुए संस्थान से ही लें।",
    },
    "romance": {
        "en": "Never send money to someone you have not met in person.",
        "hi": "जिससे आप कभी आमने-सामने नहीं मिले, उसे कभी पैसे न भेजें।",
    },
    "fake_bank_kyc": {
        "en": "Banks never ask you to update KYC through an SMS or WhatsApp link.",
        "hi": "बैंक कभी SMS या WhatsApp लिंक से KYC अपडेट नहीं करवाते।",
    },
}

SAFE_ADVICE = {
    "en": [
        "No common scam signs found, but this does NOT prove the message is safe.",
        "If it asks for money, an OTP or personal details, check first using an official number.",
    ],
    "hi": [
        "धोखे के आम निशान नहीं मिले, पर इसका मतलब यह नहीं कि मैसेज पक्का सुरक्षित है।",
        "अगर यह पैसे, OTP या निजी जानकारी मांगे, तो पहले असली नंबर से जांच करें।",
    ],
}

DISCLAIMER = {
    "en": "This is an automatic check and it can be wrong. A green result does not mean a message is safe.",
    "hi": "यह एक अपने-आप होने वाली जांच है और गलत हो सकती है। हरे निशान का मतलब यह नहीं कि मैसेज पक्का सुरक्षित है।",
}

UI = {
    "why": {"en": "Why?", "hi": "क्यों?"},
    "what_to_do": {"en": "What should I do?", "hi": "मुझे क्या करना चाहिए?"},
    "type": {"en": "Type", "hi": "प्रकार"},
    "links": {"en": "Links", "hi": "लिंक"},
    "no_flags": {"en": "No specific warning signs found.", "hi": "कोई खास चेतावनी का निशान नहीं मिला।"},
}


def t(table: dict, key: str, lang: str) -> str:
    """Look up ``table[key][lang]``, falling back to English."""
    entry = table.get(key, {})
    return entry.get(lang) or entry.get("en") or key
