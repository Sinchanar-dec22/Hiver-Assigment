"""Apple Support agent: intent classification, grounded drafting, and escalation."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


INTENTS = (
    "refund_or_charge",
    "delivery_or_order",
    "account_access",
    "device_or_software",
    "subscription",
    "privacy_or_security",
    "praise_or_other",
)

KEYWORDS = {
    "refund_or_charge": {"refund", "charged", "charge", "payment", "billing", "money", "purchase", "invoice"},
    "delivery_or_order": {"order", "delivery", "delivered", "shipping", "shipment", "package", "tracking", "arrive"},
    "account_access": {"password", "login", "log in", "locked", "account", "id", "verification", "verify"},
    "device_or_software": {"iphone", "ipad", "mac", "ios", "update", "crash", "broken", "battery", "screen", "app"},
    "subscription": {"subscription", "cancel", "renew", "trial", "monthly", "apple music", "icloud"},
    "privacy_or_security": {"hacked", "scam", "fraud", "privacy", "stolen", "security", "unknown device", "phishing"},
}

@dataclass(frozen=True)
class Case:
    text: str
    intent: str
    resolution: str
    escalation: bool
    escalation_reason: str = ""

@dataclass(frozen=True)
class AgentResult:
    intent: str
    confidence: float
    reply: str
    escalate: bool
    escalation_reason: str
    evidence: tuple[str, ...]


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def classify(text: str) -> tuple[str, float, list[str]]:
    normalized = normalize(text)
    security_hits = [keyword for keyword in KEYWORDS["privacy_or_security"] if keyword in normalized]
    if security_hits:
        return "privacy_or_security", 0.93, security_hits
    scores = {intent: 0 for intent in INTENTS}
    evidence: dict[str, list[str]] = {intent: [] for intent in INTENTS}
    for intent, keywords in KEYWORDS.items():
        for keyword in keywords:
            if keyword in normalized:
                scores[intent] += 2 if " " in keyword else 1
                evidence[intent].append(keyword)
    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]
    if best_score == 0:
        return "praise_or_other", 0.25, []
    ordered = sorted(scores.values(), reverse=True)
    margin = best_score - (ordered[1] if len(ordered) > 1 else 0)
    confidence = min(0.98, 0.52 + 0.08 * best_score + 0.05 * margin)
    return best_intent, round(confidence, 3), evidence[best_intent]


def retrieve_similar(text: str, cases: Iterable[Case], intent: str, limit: int = 3) -> list[Case]:
    query_terms = set(normalize(text).split())
    candidates = [case for case in cases if case.intent == intent]
    ranked = sorted(
        candidates,
        key=lambda case: len(query_terms.intersection(normalize(case.text).split())),
        reverse=True,
    )
    return ranked[:limit]


def draft_reply(intent: str, text: str, evidence_cases: list[Case]) -> str:
    best = evidence_cases[0].resolution if evidence_cases else {
        "refund_or_charge": "Please review the purchase in your Apple account and contact Apple Support with the order details so we can investigate the charge.",
        "delivery_or_order": "Please send us your order number by DM so Apple Support can check the delivery status.",
        "account_access": "Please use Apple's account recovery flow and contact Support by DM if you remain locked out.",
        "device_or_software": "Please share your device model and software version by DM so Apple Support can troubleshoot this with you.",
        "subscription": "Please check your subscriptions in Settings and contact Apple Support by DM if you need help cancelling or reviewing a renewal.",
        "privacy_or_security": "For your security, do not share codes publicly. Please contact Apple Support through the official support channel immediately.",
        "praise_or_other": "Thanks for reaching out. Please send us a DM with a few more details so Apple Support can help.",
    }[intent]
    return best


def should_escalate(text: str, intent: str, confidence: float) -> tuple[bool, str]:
    normalized = normalize(text)
    urgent = {"hacked", "fraud", "stolen", "scam", "unsafe", "threat", "lawsuit", "legal"}
    if any(word in normalized.split() for word in urgent):
        return True, "security, safety, or legal-risk language requires human review"
    if intent == "privacy_or_security":
        return True, "account-security cases require identity verification and human review"
    if confidence < 0.62 or intent == "praise_or_other":
        return True, "low-confidence or unsupported request needs human review"
    return False, "routine request with a confident intent and known resolution pattern"


def run_agent(text: str, cases: Iterable[Case]) -> AgentResult:
    intent, confidence, evidence = classify(text)
    similar = retrieve_similar(text, cases, intent)
    reply = draft_reply(intent, text, similar)
    escalate, reason = should_escalate(text, intent, confidence)
    return AgentResult(intent, confidence, reply, escalate, reason, tuple(evidence))
