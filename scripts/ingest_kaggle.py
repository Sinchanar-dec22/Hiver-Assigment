"""Create an AppleSupport customer-message sample from Kaggle's twcs.csv.

Usage: python scripts/ingest_kaggle.py path/to/twcs.csv --limit 5000
The source CSV is intentionally not committed because it is large and licensed by Kaggle.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

BRAND = "AppleSupport"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--output", type=Path, default=Path("data/apple_support_sample.csv"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with args.csv_path.open(encoding="utf-8", newline="", errors="replace") as source, args.output.open("w", encoding="utf-8", newline="") as target:
        reader = csv.DictReader(source)
        rows = list(reader)
        fields = reader.fieldnames or []
        text_field = "text" if "text" in fields else "Tweet content"
        required = {"tweet_id", "author_id", "inbound", "in_response_to_tweet_id"}
        missing = required - set(fields)
        if missing:
            raise ValueError(f"Expected twcs.csv columns are missing: {sorted(missing)}")

        # An inbound tweet's author is a customer, so filtering inbound rows by
        # author_id=AppleSupport is incorrect.  Instead, find AppleSupport's
        # replies and retain the inbound tweets they reply to.
        apple_replies: dict[str, str] = {}
        for row in rows:
            if row.get("author_id", "").casefold() != BRAND.casefold():
                continue
            for item in row.get("in_response_to_tweet_id", "").split(","):
                parent_id = item.strip()
                if parent_id:
                    apple_replies.setdefault(parent_id, row.get(text_field, ""))

        writer = csv.DictWriter(target, fieldnames=["tweet_id", "text", "historical_reply", "author_id", "created_at"])
        writer.writeheader()
        for row in rows:
            text = row.get(text_field, "")
            inbound = row.get("inbound", "").casefold() in {"true", "1"}
            tweet_id = row.get("tweet_id", "")
            if text and inbound and tweet_id in apple_replies:
                writer.writerow({"tweet_id": tweet_id, "text": text, "historical_reply": apple_replies[tweet_id], "author_id": row.get("author_id", ""), "created_at": row.get("created_at", "")})
                written += 1
                if written >= args.limit:
                    break
    print(f"Wrote {written} {BRAND} inbound messages to {args.output}")


if __name__ == "__main__":
    main()
