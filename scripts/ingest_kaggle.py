"""Create an Apple Support sample from a Kaggle Customer Support on Twitter CSV.

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
        fields = reader.fieldnames or []
        text_field = "text" if "text" in fields else "Tweet content"
        writer = csv.DictWriter(target, fieldnames=["text", "author_id", "created_at"])
        writer.writeheader()
        for row in reader:
            text = row.get(text_field, "")
            handle = row.get("inbound", "")
            if text and (handle.lower() in {"true", "1"} or not handle):
                writer.writerow({"text": text, "author_id": row.get("author_id", ""), "created_at": row.get("created_at", "")})
                written += 1
                if written >= args.limit:
                    break
    print(f"Wrote {written} {BRAND} inbound messages to {args.output}")


if __name__ == "__main__":
    main()
