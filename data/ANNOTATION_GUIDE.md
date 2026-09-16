# Golden-set labeling guide

1. Sample only inbound tweets that received an AppleSupport reply using `ingest_kaggle.py`.
2. Blind-label each message as exactly one of the seven README intent definitions. Use `praise_or_other` only when the message has no actionable support family.
3. Write a short, public-safe resolution pattern observed in the supplied `historical_reply`. Never copy account identifiers or other personal data.
4. Set `escalate=true` for security, fraud, theft, privacy, legal/safety, or genuinely ambiguous messages. Record uncertain cases in `label_notes`.
5. Have a second reviewer label the same 30 stratified examples independently. Do not reveal the model or first-reviewer scores until both passes are complete.

The checked-in `golden_set.csv` is a deterministic demo fixture for tests. It must be replaced with this manually labelled source-derived set before presenting headline results as assignment results.
