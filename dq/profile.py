import pandas as pd


def profile(df: pd.DataFrame) -> dict:
    """Per-column profile: type, nulls, uniqueness, numeric stats."""
    report = {"rows": len(df), "columns": {}}
    for col in df.columns:
        series = df[col]
        info = {
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_rate": round(float(series.isna().mean()), 4),
            "unique": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            info.update({
                "mean": round(float(series.mean()), 4) if series.notna().any() else None,
                "min": float(series.min()) if series.notna().any() else None,
                "max": float(series.max()) if series.notna().any() else None,
            })
        report["columns"][col] = info
    return report
