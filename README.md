# Data Quality Monitor

Profile a CSV, validate it against declarative rules, and detect drift between two snapshots - from the command line, no framework to install beyond pandas.

Built for the unglamorous part of data work: catching the batch where `age` is 950, the email column has nulls, and the average order quietly quadrupled.

## Commands

```bash
pip install -r requirements.txt
python scripts/make_sample_data.py        # writes samples/baseline.csv + samples/current.csv

python -m dq.cli profile samples/current.csv          # per-column stats, nulls, uniqueness
python -m dq.cli validate samples/current.csv samples/rules.json   # exit 1 on failure (CI-friendly)
python -m dq.cli drift samples/baseline.csv samples/current.csv    # compare two snapshots
```

## Rules format

```json
{
  "columns": {
    "order_id": {"not_null": true, "unique": true},
    "email": {"not_null": true, "regex": "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"},
    "age": {"min": 0, "max": 120},
    "plan": {"allowed_values": ["free", "pro", "team"]},
    "amount": {"min": 0}
  },
  "max_null_rate": 0.05
}
```

## Real output (bundled messy sample)

```
$ python -m dq.cli validate samples/current.csv samples/rules.json
5 check(s) failed:
  [order_id] unique: 1 duplicated values
  [email] not_null: 1 null values
  [email] regex: 1 values do not match ^[^@\s]+@[^@\s]+\.[^@\s]+$
  [age] max: 1 values above 120
  [plan] allowed_values: unexpected values: ['enterprisee']

$ python -m dq.cli drift samples/baseline.csv samples/current.csv
[amount] mean drift: 100.738 -> 167.631
```

(The messiness is injected by `scripts/make_sample_data.py` so the demo is reproducible.)

## How it works

- `dq/profile.py` - per-column dtype, null counts/rates, unique counts, numeric stats.
- `dq/checks.py` - declarative validation (`not_null`, `unique`, `min`/`max`, `allowed_values`, `regex`, table-level `max_null_rate`) plus `drift()`: relative numeric-mean shift (default >20%) and absolute null-rate shift (default >5 points) per shared column.
- `validate` exits with status 1 when any check fails, so it drops straight into a CI pipeline or an Airflow `BashOperator`.

## Honest limitations

- CSV input only (pandas `read_csv`); databases and Parquet would go through the same functions with a different loader.
- Drift detection is threshold-based, not a statistical test (no KS/PSI); it is a tripwire, not a proof.
- Regex checks apply to the string form of each value.

## Tests

```bash
pytest -q
```
