"""Run evaluation and print reproducible headline metrics."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hiver_agent import Case, run_agent  # noqa: E402


def load_cases(path: Path) -> list[Case]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [Case(row["text"], row["intent"], row["resolution"], row["escalate"].lower() == "true") for row in csv.DictReader(handle)]


def evaluate(cases: list[Case]) -> dict[str, float | int]:
    intent_correct = 0
    escalation_correct = 0
    reply_grounded = 0
    for index, case in enumerate(cases):
        # The item being evaluated must never be available for retrieval.  Otherwise
        # its hand-written resolution can be copied into its own prediction.
        retrieval_pool = cases[:index] + cases[index + 1 :]
        result = run_agent(case.text, retrieval_pool)
        intent_correct += result.intent == case.intent
        escalation_correct += result.escalate == case.escalation
        evidence = [candidate.resolution.lower() for candidate in retrieval_pool if candidate.intent == result.intent]
        reply_grounded += int(any(result.reply.lower() == resolution for resolution in evidence))
    total = len(cases)
    return {
        "examples": total,
        "intent_accuracy": round(intent_correct / total, 4),
        "escalation_accuracy": round(escalation_correct / total, 4),
        "retrieval_grounding_rate": round(reply_grounded / total, 4),
    }


def main() -> None:
    dataset = ROOT / "data" / "golden_set.csv"
    metrics = evaluate(load_cases(dataset))
    print(json.dumps(metrics, indent=2))
    output = ROOT / "results.json"
    output.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
