"""Data quality monitor.

Usage:
  python -m dq.cli profile data.csv
  python -m dq.cli validate data.csv rules.json
  python -m dq.cli drift baseline.csv current.csv
"""

import argparse
import json

import pandas as pd

from .checks import drift, run_checks
from .profile import profile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["profile", "validate", "drift"])
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()

    if args.command == "profile":
        print(json.dumps(profile(pd.read_csv(args.files[0])), indent=2))
    elif args.command == "validate":
        with open(args.files[1], encoding="utf-8") as f:
            rules = json.load(f)
        failures = run_checks(pd.read_csv(args.files[0]), rules)
        if not failures:
            print("All checks passed.")
        else:
            print(f"{len(failures)} check(s) failed:")
            for failure in failures:
                print(f"  {failure}")
            raise SystemExit(1)
    else:
        findings = drift(pd.read_csv(args.files[0]), pd.read_csv(args.files[1]))
        print("\n".join(findings) if findings else "No drift detected.")


if __name__ == "__main__":
    main()
