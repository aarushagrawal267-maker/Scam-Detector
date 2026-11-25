"""Model loading (missing / broken files) and the train/val/test split (no leakage)."""

import logging

import pytest
from fastapi.testclient import TestClient

from app import server
from scam_detector import model as model_module
from scam_detector.detector import check_message

SCAM = "Dear customer your SBI account will be blocked today. Update KYC now: http://sbi-kyc.xyz and share OTP"


@pytest.fixture
def model_path(monkeypatch):
    """Point the app at another model file; restore the real model afterwards."""

    def use(path):
        monkeypatch.setenv("SCAM_MODEL_PATH", str(path))
        model_module.load_model.cache_clear()

    yield use
    monkeypatch.delenv("SCAM_MODEL_PATH", raising=False)
    model_module.load_model.cache_clear()


def test_committed_model_loads_at_startup_and_serves_predictions():
    model_module.load_model.cache_clear()
    with TestClient(server.app) as client:  # runs the start-up (lifespan) code
        assert model_module.load_model.cache_info().currsize == 1  # loaded before any request
        health = client.get("/api/health").json()
        assert health["model_loaded"] is True
        assert health["model_version"].startswith("tfidf-logreg")
        server._hits.clear()
        body = client.post("/api/check", json={"text": SCAM, "lang": "en"}).json()
    assert body["verdict"] == "scam"
    assert 0.0 <= body["model_probability"] <= 1.0
    assert body["model_version"] == health["model_version"]


def test_missing_model_falls_back_to_rules_with_clear_message(model_path, tmp_path, caplog):
    with caplog.at_level(logging.WARNING, logger="scam_detector.model"):
        model_path(tmp_path / "nope.joblib")
        assert model_module.load_model() is None
    assert "No trained model" in caplog.text and "train_baseline" in caplog.text
    result = check_message(SCAM, lang="en")
    assert result["model_probability"] is None
    assert result["model_version"] == "rules-only"
    assert result["verdict"] in {"scam", "suspicious"}  # the rules still catch it
    with TestClient(server.app) as client:
        assert client.get("/api/health").json()["model_loaded"] is False


def test_broken_model_file_does_not_crash_requests(model_path, tmp_path, caplog):
    bad = tmp_path / "baseline.joblib"
    bad.write_bytes(b"version https://git-lfs.github.com/spec/v1\n")  # e.g. an LFS pointer, not a model
    with caplog.at_level(logging.ERROR, logger="scam_detector.model"):
        model_path(bad)
        assert model_module.load_model() is None
    assert "Could not load the model" in caplog.text
    with TestClient(server.app) as client:
        server._hits.clear()
        r = client.post("/api/check", json={"text": SCAM})
    assert r.status_code == 200
    assert r.json()["model_version"] == "rules-only"


def test_templates_never_leak_across_splits():
    """Regression: capping CloveAI templates used to drop the template group
    (pandas 3 groupby().apply), so copies of one template landed in train AND test."""
    pd = pytest.importorskip("pandas")
    from training import prepare_data as P

    rows = []
    for t in range(40):  # 40 "CloveAI" templates x 20 messages; each template is one label
        word = "x" + chr(97 + t // 26) + chr(97 + t % 26)  # numbers are blanked by template_key, words are not
        rows += [{"text": f"{word} pay rs {n} now" if t % 2 else f"{word} bill of rs {n} paid",
                  "label": t % 2, "source": "clove", "language": "en", "category": "none"} for n in range(20)]
    for i in range(300):  # unrelated other-source messages
        rows.append({"text": f"msg {chr(97 + i % 26)}{chr(97 + i // 26)} hello" + "!" * (i % 3),
                     "label": int(i % 4 == 0), "source": "uci", "language": "en", "category": "none"})
    df = P.dedupe_and_group(pd.DataFrame(rows))

    clove = df[df.source == "clove"]
    assert clove["group"].notna().all()
    assert clove.groupby("group").size().max() <= P.CLOVE_CAP_PER_TEMPLATE

    out = P.split(df)
    P.check_no_leakage(out)  # raises if any template group is in two splits
    assert set(out.split) == {"train", "val", "test"}

    out.loc[out.index[0], "group"] = None
    with pytest.raises(AssertionError):
        P.check_no_leakage(out)
