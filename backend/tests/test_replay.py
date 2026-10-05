"""Unit tests for backend/ichnoscope/replay.py."""

from pathlib import Path

from ichnoscope.replay import replay_fixture


def test_replay_existing_fixture(tmp_path: Path, capsys):
    fixture = Path("backend/fixtures/bug1_keyerror_payment.json")
    db_file = str(tmp_path / "replay_test.db")

    code = replay_fixture(fixture, dry_run=True, db_path=db_file)
    assert code == 0

    captured = capsys.readouterr()
    assert "KeyError" in captured.out
    assert "services/payment.py:84" in captured.out
    assert "--- Pipeline Logs ---" in captured.out


def test_replay_missing_fixture(capsys):
    code = replay_fixture("nonexistent_fixture.json")
    assert code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_replay_invalid_json(tmp_path: Path, capsys):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text("{bad json", encoding="utf-8")

    code = replay_fixture(bad_file)
    assert code == 1
    captured = capsys.readouterr()
    assert "Failed to read JSON fixture" in captured.err
