import re

import pandas as pd


class CheckFailure:
    def __init__(self, column: str, check: str, detail: str):
        self.column = column
        self.check = check
        self.detail = detail

    def __str__(self) -> str:
        return f"[{self.column}] {self.check}: {self.detail}"


def run_checks(df: pd.DataFrame, rules: dict) -> list[CheckFailure]:
    """Validate a DataFrame against declarative rules.

    rules = {
      "columns": {
        "age":   {"not_null": true, "min": 0, "max": 120},
        "email": {"not_null": true, "unique": true, "regex": "^[^@]+@[^@]+$"},
        "plan":  {"allowed_values": ["free", "pro", "team"]}
      },
      "max_null_rate": 0.05
    }
    """
    failures: list[CheckFailure] = []
    for column, checks in rules.get("columns", {}).items():
        if column not in df.columns:
            failures.append(CheckFailure(column, "exists", "column is missing"))
            continue
        series = df[column]
        if checks.get("not_null"):
            count = int(series.isna().sum())
            if count:
                failures.append(CheckFailure(column, "not_null", f"{count} null values"))
        if checks.get("unique"):
            dupes = int(series.dropna().duplicated().sum())
            if dupes:
                failures.append(CheckFailure(column, "unique", f"{dupes} duplicated values"))
        if "min" in checks:
            bad = series.dropna() < checks["min"]
            if bad.any():
                failures.append(CheckFailure(column, "min", f"{int(bad.sum())} values below {checks['min']}"))
        if "max" in checks:
            bad = series.dropna() > checks["max"]
            if bad.any():
                failures.append(CheckFailure(column, "max", f"{int(bad.sum())} values above {checks['max']}"))
        if "allowed_values" in checks:
            bad = ~series.dropna().isin(checks["allowed_values"])
            if bad.any():
                examples = sorted(series.dropna()[bad.values].unique())[:5]
                failures.append(CheckFailure(column, "allowed_values", f"unexpected values: {list(examples)}"))
        if "regex" in checks:
            pattern = re.compile(checks["regex"])
            bad = ~series.dropna().astype(str).str.match(pattern)
            if bad.any():
                failures.append(CheckFailure(column, "regex", f"{int(bad.sum())} values do not match {checks['regex']}"))
    max_null_rate = rules.get("max_null_rate")
    if max_null_rate is not None:
        for column in df.columns:
            rate = float(df[column].isna().mean())
            if rate > max_null_rate:
                failures.append(CheckFailure(column, "max_null_rate", f"null rate {rate:.3f} > {max_null_rate}"))
    return failures


def drift(baseline: pd.DataFrame, current: pd.DataFrame, mean_shift: float = 0.2, null_shift: float = 0.05) -> list[str]:
    """Compare two snapshots: flag numeric-mean and null-rate drift per shared column."""
    findings = []
    for column in baseline.columns.intersection(current.columns):
        base, cur = baseline[column], current[column]
        if pd.api.types.is_numeric_dtype(base) and base.notna().any() and cur.notna().any():
            b_mean, c_mean = float(base.mean()), float(cur.mean())
            if b_mean != 0 and abs(c_mean - b_mean) / abs(b_mean) > mean_shift:
                findings.append(f"[{column}] mean drift: {b_mean:.3f} -> {c_mean:.3f}")
        b_null, c_null = float(base.isna().mean()), float(cur.isna().mean())
        if abs(c_null - b_null) > null_shift:
            findings.append(f"[{column}] null-rate drift: {b_null:.3f} -> {c_null:.3f}")
    return findings
