from scam_detector.detector import check_message
from scam_detector.rules import combine_with_url_risk, find_red_flags


def flags(text):
    return find_red_flags(text).flags


def test_otp_request_is_flagged_in_three_languages():
    assert "asks_for_otp" in flags("Please share the OTP you received to cancel the transaction")
    assert "asks_for_otp" in flags("jo OTP aaya hai woh bata dijiye")
    assert "asks_for_otp" in flags("आया हुआ ओटीपी बताएं")


def test_do_not_share_otp_is_not_a_red_flag():
    assert "asks_for_otp" not in flags("Your OTP is 123456. Do not share this OTP with anyone.")


def test_digital_arrest_and_secrecy():
    f = flags("This is CBI. You are under digital arrest. Do not tell anyone.")
    assert "authority_threat" in f and "secrecy" in f


def test_family_new_number():
    assert "new_number_family" in flags("Hi mom this is my new number, send money urgently")


def test_safe_signals_soften_rule_score():
    genuine = "Please complete your KYC by visiting your nearest branch with documents."
    r = combine_with_url_risk(find_red_flags(genuine), [])
    assert r.safe_signals and r.score < 0.2


def test_safe_signals_never_soften_otp_requests():
    text = "Visit your nearest branch later, but first share the OTP now to stop the block"
    r = combine_with_url_risk(find_red_flags(text), [])
    assert r.score >= 0.65


def test_clear_scam_gets_red_verdict_and_category():
    r = check_message("Your SBI account will be blocked today. Update KYC now: http://sbi-kyc.xyz/u", online_link_check=False)
    assert r["verdict"] == "scam"
    assert r["category"] == "fake_bank_kyc"
    assert r["emoji"] == "🔴"
    assert r["links"][0]["url"].startswith("hxxp")  # links are always shown defanged


def test_ordinary_message_is_likely_safe_never_safe():
    r = check_message("Beta dinner ke liye 8 baje tak aa jana", online_link_check=False)
    assert r["verdict"] == "likely_safe"
    assert "NOT" in check_message("See you at 5 pm at the park", lang="en", online_link_check=False)["headline"]
    assert r["category"] is None


def test_reply_is_short_and_has_words_not_just_colour():
    r = check_message("You have won Rs 25 lakh in KBC lottery! Pay registration fee to claim.", lang="en",
                      online_link_check=False)
    lines = r["reply_text"].splitlines()
    assert len(lines) <= 5
    assert "SCAM" in lines[0] or "SUSPICIOUS" in lines[0]


def test_hindi_reply():
    r = check_message("आपका खाता आज बंद हो जाएगा, तुरंत केवाईसी अपडेट करें", lang="hi", online_link_check=False)
    assert r["reply_language"] == "hi"
    assert any("ऀ" <= ch <= "ॿ" for ch in r["reply_text"])


def test_scam_advice_always_mentions_1930():
    r = check_message("Send OTP now or your account will be blocked", lang="en", online_link_check=False)
    assert any("1930" in a for a in r["advice"])


def test_empty_message_raises():
    import pytest

    with pytest.raises(ValueError):
        check_message("   ")
