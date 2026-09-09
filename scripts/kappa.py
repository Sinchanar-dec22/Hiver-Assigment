"""Compute Cohen's kappa for a two-column binary human/judge annotation CSV."""
from __future__ import annotations

import argparse
import csv


def kappa(left: list[int], right: list[int]) -> float:
    n = len(left)
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
    left = [int(row[args.human]) for row in rows]
    right = [int(row[args.judge]) for row in rows]
    print(f"n={len(rows)} raw_agreement={sum(a == b for a, b in zip(left, right)) / len(rows):.3f} kappa={kappa(left, right):.3f}")


if __name__ == "__main__":
    main()
