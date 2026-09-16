"""Create a blinded, intent-stratified human-review sheet for LLM-judge calibration."""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hiver_agent import Case, INTENTS, run_agent  # noqa: E402


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def stratified_rows(rows: list[dict[str, str]], size: int, seed: int) -> list[dict[str, str]]:
    if size < len(INTENTS):
        raise ValueError(f"size must be at least {len(INTENTS)}")
    groups = {intent: [] for intent in INTENTS}
    for row in rows:
        groups.get(row.get("intent", ""), []).append(row)
    missing = [intent for intent, group in groups.items() if not group]
    if missing:
        raise ValueError(f"Cannot stratify: missing intents {missing}")
    rng = random.Random(seed)
    for group in groups.values():
        rng.shuffle(group)
    selected: list[dict[str, str]] = []
    while len(selected) < size:
        progressed = False
        for intent in INTENTS:
            if groups[intent] and len(selected) < size:
                selected.append(groups[intent].pop())
                progressed = True
        if not progressed:
            raise ValueError(f"Only {len(selected)} unique rows available; need {size}")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "golden_set.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "agreement_human_template.csv")
    parser.add_argument("--size", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260910)
    args = parser.parse_args()

    rows = load_rows(args.input)
    chosen = stratified_rows(rows, args.size, args.seed)
    cases = [Case(row["text"], row["intent"], row["resolution"], row["escalate"].lower() == "true") for row in rows]
    fields = ["id", "text", "predicted_intent", "draft_reply", "escalation_decision", "escalation_reason", "historical_resolution", "human_grounded", "human_relevant", "human_safe", "human_escalation_appropriate", "human_reason"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in chosen:
            case = Case(row["text"], row["intent"], row["resolution"], row["escalate"].lower() == "true")
            result = run_agent(case.text, [other for other in cases if other.text != case.text])
            writer.writerow({
                "id": row["id"], "text": case.text, "predicted_intent": result.intent,
                "draft_reply": result.reply, "escalation_decision": result.escalate,
                "escalation_reason": result.escalation_reason, "historical_resolution": case.resolution,
            })
    print(f"Wrote {args.output} for an independent reviewer; do not share LLM scores before review.")


if __name__ == "__main__":
    main()
