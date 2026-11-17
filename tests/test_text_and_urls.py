from scam_detector.text_utils import anonymise, defang_url, detect_language, find_urls, normalise
from scam_detector.urls import analyse_url, registered_domain


def test_language_detection():
    assert detect_language("Your parcel is out for delivery") == "en"
    assert detect_language("आपका खाता बंद हो जाएगा") == "hi"
    assert detect_language("Aapka account band ho jayega, turant kare") == "hinglish"


def test_normalise_removes_zero_width_and_extra_spaces():
    assert normalise("O​T P   now") == "OT P now"


def test_find_urls_including_bare_domains():
    text = "Click http://sbi-kyc.xyz/login or bit.ly/abc now. Also www.example.com."
    assert find_urls(text) == ["http://sbi-kyc.xyz/login", "bit.ly/abc", "www.example.com"]


def test_defang():
    assert defang_url("https://evil.com/x") == "hxxps://evil[.]com/x"


def test_anonymise_removes_personal_details():
    out = anonymise("Call 9876543210 or mail a.b@gmail.com, a/c 1234 5678 9012, see http://x.com")
    assert "9876543210" not in out and "[PHONE]" in out
    assert "[EMAIL]" in out
    assert "1234 5678 9012" not in out
    assert "x[.]com" in out


def test_registered_domain():
    assert registered_domain("secure.sbi.co.in") == "sbi.co.in"
    assert registered_domain("a.b.example.com") == "example.com"


def test_lookalike_brand_is_high_risk():
    r = analyse_url("http://sbi-kyc-update.xyz/login")
    assert r.risk == "high"
    assert "brand_lookalike" in r.reasons and "suspicious_tld" in r.reasons


def test_official_domain_is_not_lookalike():
    r = analyse_url("https://www.onlinesbi.sbi/")
    assert r.official and r.risk == "low"
    assert analyse_url("https://uidai.gov.in").official


def test_shortener_ip_apk():
    assert "shortener" in analyse_url("bit.ly/abc").reasons
    assert analyse_url("http://192.168.10.5/pay").risk == "high"
    assert "apk_download" in analyse_url("http://x.com/bill.apk").reasons
