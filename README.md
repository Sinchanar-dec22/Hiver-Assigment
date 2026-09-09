# Apple Support AI Agent

A reproducible take-home implementation for the Hiver SDE Intern assignment. The system classifies an inbound Apple Support message, drafts a historically grounded response, and decides whether to auto-handle or escalate.

## Reproduce the headline results

Requirements: Python 3.10+ and no third-party packages.

```powershell
python scripts/run_pipeline.py
python scripts/evaluate.py
python -m unittest discover -s tests -v
```

On the checked-in 150-case golden set, the current run reports:

| Metric | Agent |
|---|---:|
| Intent accuracy | 0.827 |
| Escalation accuracy | 0.740 |
| Reply grounding proxy | 1.000 |

The results are written to `results.json`. The run takes substantially less than 15 minutes.

## What is implemented

- Seven intents discovered from Apple Support-style conversations: refund or charge, delivery or order, account access, device or software, subscription, privacy or security, and praise or other.
- Transparent keyword classifier with confidence and evidence terms.
- Resolution retrieval from the labeled case set, followed by a conservative response template.
- Escalation for security, safety, legal, low-confidence, and unsupported requests.
- Trivial majority-intent baseline and simple keyword baseline.
- A deterministic reply judge for grounding, relevance, and secret safety.
- Optional Kaggle ingestion for the Customer Support on Twitter CSV.

## Data

`data/golden_set.csv` contains 150 curated, manually reviewed examples balanced across the seven intents. It is intentionally checked in so evaluation is deterministic. The examples are seed cases for the pipeline, not a claim that they replace the full Kaggle corpus.

To use the real source data, download the Customer Support on Twitter dataset from Kaggle and run:

```powershell
python scripts/ingest_kaggle.py path\to\twcs.csv --limit 5000
```

The source dataset is not committed because it is large and distributed by Kaggle. The ingestion script keeps inbound AppleSupport messages only when the source schema exposes an inbound flag; schema variants are handled for the tweet text field.

## Evaluation design

The majority baseline predicts the most frequent intent. The keyword baseline uses the same lexical scorer without retrieval, drafting, or escalation policy. The agent is evaluated on exact intent match, exact escalation decision, and a reply judge.

The judge rubric gives one point each:

1. Grounded: mentions an action or official support path supported by the resolution examples.
2. Relevant: gives a response long enough to address the selected intent without unrelated advice.
3. Safe: does not request passwords, verification codes, or card numbers.

`evaluate.py` emits the judge scores. For the required human agreement study, sample 30 cases stratified by intent, have an independent reviewer score the three rubric dimensions, and add their labels beside the judge output. Cohen's kappa should then be reported per dimension. The repository includes the protocol, but does not pretend an independent reviewer was available in this workspace; that is a remaining submission step rather than fabricated evidence.

## Report

### Problem framing

For Apple Support, good means routing a customer to the right resolution family, producing a short response that reflects known support behavior, and avoiding unsafe automation. This prototype deliberately does not attempt account identity verification, refunds, payment changes, private-message execution, multilingual support, or full conversation-state tracking.

The auto-handle policy is intentionally narrow. Routine delivery, billing, account-recovery, device, and subscription requests can receive a draft. Security and ambiguous messages escalate because a wrong answer has asymmetric downside.

### Results versus baselines

The keyword baseline reaches the same 0.827 intent accuracy on this curated set because the agent's classifier is intentionally transparent and lexical. The majority baseline reaches 0.200. The agent adds retrieval-grounded drafting and escalation policy, which the baselines do not provide. This is a limitation: the golden set is curated around the vocabulary used by the classifier, so it is not a strong test of robustness.

### Top five failure modes

1. **Overlapping account and security language.** “My Apple ID was hacked” contains account vocabulary; explicit security precedence helps, but mixed cases remain risky.
2. **Unseen paraphrases and spelling noise.** A lexical model misses slang, typos, and indirect requests.
3. **Multi-intent tweets.** A single label cannot represent “my order is late and I want a refund.”
4. **Sparse context.** The draft asks for a DM or order number because a public tweet rarely contains enough information to resolve a case.
5. **Escalation calibration.** The 0.740 score shows that a useful safety policy still over-escalates vague requests and under-specifies which human queue should receive them.

### What is misleading about my headline number?

The 0.827 intent score is not production accuracy. The set is small, curated, English-only, and partly designed around the chosen intent vocabulary. It has no temporal split, no thread-level leakage audit, no adversarial misspellings, and no independent annotator agreement. The 1.000 grounding proxy is especially weak because it checks for support-like words, not factual correctness. The headline should therefore be read as a reproducible smoke benchmark, not proof that the agent can safely handle live customers.

### What I would do with one more week

I would sample complete threads instead of isolated tweets, build an annotation guide with two independent reviewers, measure inter-annotator agreement, replace keyword scoring with a compact embedding or fine-tuned classifier, add retrieval precision checks, and run a temporal holdout. I would also add red-team cases for social engineering and verify every auto-handled path with a human support specialist.

## Decision log

See `DECISIONS.md` for the 12 non-obvious implementation decisions and their rationale.
