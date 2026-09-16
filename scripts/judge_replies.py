"""Run the documented LLM judge and persist per-example rubric scores.

This optional command requires OPENAI_API_KEY and intentionally is not part of the
under-15-minute offline headline run.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hiver_agent import Case, run_agent  # noqa: E402

RUBRIC = (ROOT / "LLM_JUDGE_RUBRIC.md").read_text(encoding="utf-8")


def judge(prompt: str, model: str) -> dict[str, object]:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("Set OPENAI_API_KEY before running the LLM judge")
    payload = json.dumps({"model": model, "input": prompt, "text": {"format": {"type": "json_object"}}}).encode()
    request = Request(
        "https://api.openai.com/v1/responses", payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST",
    )
    with urlopen(request, timeout=60) as response:  # nosec B310 - fixed HTTPS API endpoint
        body = json.load(response)
    return json.loads(body["output_text"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "golden_set.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "llm_judge_scores.csv")
    parser.add_argument("--model", default="gpt-5-mini")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    cases = [Case(row["text"], row["intent"], row["resolution"], row["escalate"].lower() == "true") for row in rows]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "grounded", "relevant", "safe", "escalation_appropriate", "reason"])
        writer.writeheader()
        for index, case in enumerate(cases, start=1):
            result = run_agent(case.text, [other for other in cases if other is not case])
            prompt = RUBRIC + "\n\n" + (
                f"Customer message: {case.text}\nPredicted intent: {result.intent}\n"
                f"Draft reply: {result.reply}\nHistorical resolution evidence: {case.resolution}\n"
                f"Escalation decision: {result.escalate} ({result.escalation_reason})"
            )
            score = judge(prompt, args.model)
            # Preserve the source identifier so agreement rows can be joined
            # safely even when the input file has been reordered.
            case_id = rows[index - 1].get("id", index)
            writer.writerow({"id": case_id, **{key: score.get(key, "") for key in writer.fieldnames if key != "id"}})
    print(f"Wrote LLM judge scores to {args.output}")


if __name__ == "__main__":
    main()
