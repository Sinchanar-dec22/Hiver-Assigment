"""Create a reproducible blind-labeling template from AppleSupport source messages."""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Output from ingest_kaggle.py")
    parser.add_argument("--output", type=Path, default=Path("data/golden_annotation_template.csv"))
    parser.add_argument("--size", type=int, default=180, choices=range(150, 251))
    parser.add_argument("--seed", type=int, default=20260910)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("text", "").strip()]
    if len(rows) < args.size:
        raise ValueError(f"Need at least {args.size} AppleSupport messages; found {len(rows)}")

    random.Random(args.seed).shuffle(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "tweet_id", "text", "historical_reply", "intent", "resolution", "escalate", "label_notes"],
        )
        writer.writeheader()
        for number, row in enumerate(rows[: args.size], start=1):
            writer.writerow({"id": number, "tweet_id": row.get("tweet_id", ""), "text": row["text"], "historical_reply": row.get("historical_reply", "")})
    print(f"Wrote {args.size} blind-label rows to {args.output}")


if __name__ == "__main__":
    main()
