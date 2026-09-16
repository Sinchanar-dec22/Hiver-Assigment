"""Fail fast when the required evidence artifacts are incomplete or malformed."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hiver_agent import INTENTS  # noqa: E402

GOLDEN_FIELDS = {"id", "tweet_id", "text", "historical_reply", "intent", "resolution", "escalate", "label_notes"}
AGREEMENT_FIELDS = {"id", "human_grounded", "human_relevant", "human_safe", "human_escalation_appropriate", "judge_grounded", "judge_relevant", "judge_safe", "judge_escalation_appropriate"}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", type=Path, default=ROOT / "data" / "golden_set.csv")
    parser.add_argument("--agreement", type=Path, default=ROOT / "data" / "agreement_scores.csv")
    args = parser.parse_args()
    errors: list[str] = []
    require(args.golden.exists(), f"Missing golden set: {args.golden}", errors)
    if args.golden.exists():
        golden = rows(args.golden)
        fields = set(golden[0]) if golden else set()
        require(GOLDEN_FIELDS <= fields, f"Golden set must include {sorted(GOLDEN_FIELDS)}", errors)
        require(150 <= len(golden) <= 250, f"Golden set must contain 150-250 rows; found {len(golden)}", errors)
        ids = [row.get("id", "") for row in golden]
        tweets = [row.get("tweet_id", "") for row in golden]
        require(all(ids) and len(ids) == len(set(ids)), "Golden-set IDs must be present and unique", errors)
        require(all(tweets) and len(tweets) == len(set(tweets)), "Golden-set tweet_ids must be present and unique source IDs", errors)
        checks = {
            "customer text": lambda row: row.get("text", "").strip() != "",
            "historical reply": lambda row: row.get("historical_reply", "").strip() != "",
            "hand-written resolution": lambda row: row.get("resolution", "").strip() != "",
            "valid intent": lambda row: row.get("intent") in INTENTS,
            "true/false escalation": lambda row: row.get("escalate", "").lower() in {"true", "false"},
        }
        for label, check in checks.items():
            failed = sum(not check(row) for row in golden)
            require(failed == 0, f"Golden set has {failed} rows without {label}", errors)
    require(args.agreement.exists(), f"Missing blinded human/LLM agreement file: {args.agreement}", errors)
    if args.agreement.exists():
        agreement = rows(args.agreement)
        fields = set(agreement[0]) if agreement else set()
        require(AGREEMENT_FIELDS <= fields, f"Agreement file must include {sorted(AGREEMENT_FIELDS)}", errors)
        valid = [row for row in agreement if all(row.get(field) in {"0", "1"} for field in AGREEMENT_FIELDS - {"id"})]
        require(len(valid) >= 30, f"Need at least 30 fully blind-scored agreement rows; found {len(valid)}", errors)
    if errors:
        print("SUBMISSION CHECK FAILED")
        print("\n".join(f"- {error}" for error in errors))
        raise SystemExit(1)
    print("SUBMISSION CHECK PASSED: golden set and human/LLM agreement evidence are present.")


if __name__ == "__main__":
    main()
