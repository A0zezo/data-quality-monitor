"""Generate two synthetic order snapshots: a clean baseline and a messy current batch."""

import random

import pandas as pd

random.seed(7)
plans = ["free", "pro", "team"]


def make(rows, messy=False):
    data = {
        "order_id": range(1, rows + 1),
        "email": [f"user{i}@example.com" for i in range(rows)],
        "age": [random.randint(18, 70) for _ in range(rows)],
        "plan": [random.choice(plans) for _ in range(rows)],
        "amount": [round(random.uniform(5, 200), 2) for _ in range(rows)],
    }
    df = pd.DataFrame(data)
    if messy:
        df.loc[3, "email"] = None
        df.loc[5, "email"] = "not-an-email"
        df.loc[8, "age"] = 950
        df.loc[11, "plan"] = "enterprisee"
        df.loc[12, "plan"] = None
        df = pd.concat([df, df.iloc[[20]]], ignore_index=True)  # duplicate order_id
        df.loc[df.sample(frac=0.2, random_state=1).index, "amount"] *= 4  # drift
    return df


if __name__ == "__main__":
    make(200).to_csv("samples/baseline.csv", index=False)
    make(200, messy=True).to_csv("samples/current.csv", index=False)
    print("wrote samples/baseline.csv and samples/current.csv")
