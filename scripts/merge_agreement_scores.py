"""Join blinded human labels with LLM-judge scores by stable example ID."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


DIMENSIONS = ("grounded", "relevant", "safe", "escalation_appropriate")


def load(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--human", type=Path, default=Path("data/agreement_human_template.csv"))
    parser.add_argument("--judge", type=Path, default=Path("data/llm_judge_scores.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/agreement_scores.csv"))
    args = parser.parse_args()
    human_rows = load(args.human)
    judge_by_id = {row.get("id", ""): row for row in load(args.judge)}
    if len(judge_by_id) != len(load(args.judge)):
        raise ValueError("Judge-score file contains duplicate IDs")
    fields = ["id"] + [f"human_{d}" for d in DIMENSIONS] + [f"judge_{d}" for d in DIMENSIONS]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for human in human_rows:
            judge = judge_by_id.get(human.get("id", ""))
            if not judge:
                raise ValueError(f"No judge score for human-review ID {human.get('id')}")
            writer.writerow({"id": human["id"], **{f"human_{d}": human.get(f"human_{d}", "") for d in DIMENSIONS}, **{f"judge_{d}": judge.get(d, "") for d in DIMENSIONS}})
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
