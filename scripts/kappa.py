"""Compute raw agreement and Cohen's kappa for a binary rubric dimension."""
from __future__ import annotations

import argparse
import csv


def kappa(left: list[int], right: list[int]) -> float:
    n = len(left)
    if n == 0:
        raise ValueError("No scored rows were found")
    observed = sum(a == b for a, b in zip(left, right)) / n
    p_left = sum(left) / n
    p_right = sum(right) / n
    expected = p_left * p_right + (1 - p_left) * (1 - p_right)
    return 1.0 if expected == 1 else (observed - expected) / (1 - expected)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--human", default="human")
    parser.add_argument("--judge", default="judge")
    args = parser.parse_args()
    with open(args.csv_path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    scored = [row for row in rows if row.get(args.human, "") in {"0", "1"} and row.get(args.judge, "") in {"0", "1"}]
    left = [int(row[args.human]) for row in scored]
    right = [int(row[args.judge]) for row in scored]
    print(f"n={len(scored)} raw_agreement={sum(a == b for a, b in zip(left, right)) / len(scored):.3f} kappa={kappa(left, right):.3f}")


if __name__ == "__main__":
    main()
