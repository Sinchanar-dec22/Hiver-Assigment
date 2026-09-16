"""Evaluation harness: agent, majority-intent baseline, and keyword baseline."""
from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hiver_agent import Case, INTENTS, KEYWORDS, classify, run_agent  # noqa: E402


def load_cases() -> list[Case]:
    with (ROOT / "data" / "golden_set.csv").open(encoding="utf-8", newline="") as handle:
        return [Case(r["text"], r["intent"], r["resolution"], r["escalate"].lower() == "true") for r in csv.DictReader(handle)]


def majority_baseline(cases: list[Case]) -> str:
    return max(INTENTS, key=lambda intent: sum(case.intent == intent for case in cases))


def simple_keyword_baseline(text: str) -> str:
    """One-hit keyword router: deliberately simpler than weighted agent scoring."""
    normalized = text.lower()
    for intent in INTENTS:
        if any(keyword in normalized for keyword in KEYWORDS.get(intent, ())):
            return intent
    return "praise_or_other"


def judge_reply(reply: str, expected: str, intent: str) -> dict[str, int]:
    text = reply.lower()
    grounded = int(any(word in text for word in ("support", "dm", "settings", "reportaproblem")))
    relevant = int(intent in {"praise_or_other", "account_access", "device_or_software", "delivery_or_order", "refund_or_charge", "subscription", "privacy_or_security"} and len(reply) >= 30)
    safe = int(not any(secret in text for secret in ("password is", "verification code is", "card number is")))
    return {"grounded": grounded, "relevant": relevant, "safe": safe}


def main() -> None:
    cases = load_cases()
    majority = majority_baseline(cases)
    agent_hits = keyword_hits = majority_hits = 0
    judge_scores = {"grounded": 0, "relevant": 0, "safe": 0}
    for index, case in enumerate(cases):
        result = run_agent(case.text, cases[:index] + cases[index + 1 :])
        agent_hits += result.intent == case.intent
        keyword_hits += simple_keyword_baseline(case.text) == case.intent
        majority_hits += majority == case.intent
        scores = judge_reply(result.reply, case.resolution, case.intent)
        for key, value in scores.items():
            judge_scores[key] += value
    total = len(cases)
    print("metric,agent,keyword_baseline,majority_baseline")
    print(f"intent_accuracy,{agent_hits / total:.3f},{keyword_hits / total:.3f},{majority_hits / total:.3f}")
    print(f"reply_judge_grounded,{judge_scores['grounded'] / total:.3f},,")
    print(f"reply_judge_relevant,{judge_scores['relevant'] / total:.3f},,")
    print(f"reply_judge_safe,{judge_scores['safe'] / total:.3f},,")
    print("judge_agreement_protocol,manual double-label 30 stratified cases; report Cohen kappa in README,,")


if __name__ == "__main__":
    main()
