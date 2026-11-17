import pytest

from scam_detector import stats


@pytest.fixture(autouse=True)
def temp_stats_db(tmp_path, monkeypatch):
    """Every test gets its own empty stats database."""
    db = tmp_path / "stats.db"
    monkeypatch.setattr(stats, "DB_PATH", db)
    return db
