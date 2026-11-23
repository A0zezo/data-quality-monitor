import pandas as pd

from dq.checks import drift, run_checks
from dq.profile import profile


def frame():
    return pd.DataFrame({
        "id": [1, 2, 2, 4],
        "email": ["a@x.com", None, "bad", "d@x.com"],
        "age": [25, 30, 200, 40],
        "plan": ["free", "pro", "pro", "gold"],
    })


RULES = {
    "columns": {
        "id": {"not_null": True, "unique": True},
        "email": {"not_null": True, "regex": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
        "age": {"min": 0, "max": 120},
        "plan": {"allowed_values": ["free", "pro"]},
    }
}


def test_checks_catch_everything():
    failures = run_checks(frame(), RULES)
    kinds = {(f.column, f.check) for f in failures}
    assert ("id", "unique") in kinds
    assert ("email", "not_null") in kinds
    assert ("email", "regex") in kinds
    assert ("age", "max") in kinds
    assert ("plan", "allowed_values") in kinds


def test_clean_frame_passes():
    clean = pd.DataFrame({"id": [1, 2], "email": ["a@x.com", "b@x.com"], "age": [20, 30], "plan": ["free", "pro"]})
    assert run_checks(clean, RULES) == []


def test_profile_counts_nulls():
    report = profile(frame())
    assert report["rows"] == 4
    assert report["columns"]["email"]["null_count"] == 1


def test_drift_flags_mean_shift():
    base = pd.DataFrame({"amount": [100.0] * 50, "x": list(range(50))})
    cur = pd.DataFrame({"amount": [200.0] * 50, "x": list(range(50))})
    findings = drift(base, cur)
    assert any("amount" in f for f in findings)
    assert not any("x" in f for f in findings)
