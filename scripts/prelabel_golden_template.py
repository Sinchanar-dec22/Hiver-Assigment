"""Create auditable initial labels for a source-derived annotation template.

These are deliberately marked as AI-assisted prelabels. A human must audit them
before representing the set as hand-labelled in a submission.
"""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def has(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def label(text: str, reply: str) -> tuple[str, bool]:
    """Independent, conservative rules for initial human-review labels."""
    value = norm(f"{text} {reply}")
    if has(value, ("hacked", "hack", "fraud", "scam", "phishing", "stolen", "privacy", "security", "unauthorized", "unknown charge", "unknown device")):
        return "privacy_or_security", True
    if has(value, ("refund", "charged", "charge", "billing", "billed", "payment", "paying", "credit card", "debit card", "purchase", "receipt")):
        return "refund_or_charge", False
    if has(value, ("order", "delivery", "deliver", "shipping", "shipment", "package", "tracking", "preorder")):
        return "delivery_or_order", False
    if has(value, ("subscription", "apple music", "icloud storage", "renew", "cancell", "trial", "monthly plan")):
        return "subscription", False
    if has(value, ("password", "apple id", "sign in", "login", "log in", "locked", "verification", "two factor", "2fa")):
        return "account_access", False
    if has(value, ("iphone", "ipad", "macbook", "imac", "ios", "watch", "airpods", "battery", "screen", "crash", "update", "app", "call", "sound", "device")):
        return "device_or_software", False
    ambiguous = len(norm(text).split()) < 5 or has(value, ("help", "what is this", "problem", "issue"))
    return "praise_or_other", ambiguous


def resolution(reply: str, intent: str) -> str:
    value = norm(reply)
    if "dm" in value or "direct message" in value:
        return "Ask the customer to contact Apple Support by DM with the relevant details so the case can be investigated privately."
    if has(value, ("support apple com", "getsupport", "contact", "reach out")):
        return "Direct the customer to the official Apple Support contact channel for case-specific assistance."
    if "update" in value:
        return "Ask the customer to check the relevant software update and provide device details for further troubleshooting."
    if "restart" in value:
        return "Ask the customer to restart the device and share the outcome if the issue continues."
    if intent == "privacy_or_security":
        return "Advise the customer to use official Apple Support channels and avoid sharing sensitive information publicly."
    if intent == "refund_or_charge":
        return "Ask for the purchase details through a private Apple Support channel so the charge can be reviewed."
    if intent == "delivery_or_order":
        return "Ask for the order details through a private Apple Support channel so the order status can be checked."
    if intent == "account_access":
        return "Guide the customer through the official account-recovery or Apple Support flow for account access help."
    if intent == "subscription":
        return "Direct the customer to the relevant subscription settings or Apple Support channel for account-specific help."
    if intent == "device_or_software":
        return "Ask for the device model, software version, and issue details so Apple Support can troubleshoot."
    return "Invite the customer to share more details with Apple Support so the request can be routed correctly."


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.input
    with args.input.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames or []
        rows = list(reader)
    required = {"text", "historical_reply", "intent", "resolution", "escalate", "label_notes"}
    if not required <= set(fields):
        raise ValueError(f"Missing required columns: {sorted(required - set(fields))}")
    for row in rows:
        intent, escalate = label(row["text"], row["historical_reply"])
        row["intent"] = intent
        row["resolution"] = resolution(row["historical_reply"], intent)
        row["escalate"] = str(escalate).lower()
        row["label_notes"] = "AI-assisted initial label from customer text and linked AppleSupport reply; human audit required before submission."
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} AI-assisted initial labels to {output}")


if __name__ == "__main__":
    main()
