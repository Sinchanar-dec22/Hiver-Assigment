# Apple Support AI Agent

A reproducible Hiver SDE Intern assignment implementation. It classifies an inbound Apple Support message, retrieves a historically observed resolution pattern, drafts a public-safe reply, and states whether the case must be escalated.

## Run the offline smoke benchmark

Python 3.10+ is the only requirement.

```powershell
python scripts/run_pipeline.py
python scripts/evaluate.py
python -m unittest discover -s tests -v
```

The checked-in fixture has 150 cases and runs in seconds. `results.json` records intent accuracy, escalation accuracy, and a leave-one-out retrieval-grounding rate. These figures are smoke-test results only, not an assignment headline result.

## What is implemented

- Seven data-oriented intents: refund or charge, delivery or order, account access, device or software, subscription, privacy or security, and praise or other.
- A transparent weighted keyword classifier with evidence terms and security precedence.
- Leave-one-out resolution retrieval, conservative reply drafting, and an explicit escalation reason.
- Majority and deliberately simpler first-keyword baselines.
- An offline judge smoke test, an LLM-judge rubric and runner, and a Cohen's-kappa utility.
- Reproducible extraction of actual inbound tweets that received an `AppleSupport` reply.

## Required source-derived golden set

`data/golden_set.csv` is a deterministic demo fixture for tests. It is not evidence of a source-derived hand-labelled set, and it must not be presented as the submission benchmark. Claiming otherwise would be misleading.

Download Kaggle's Customer Support on Twitter `twcs.csv`, then create the real 150-250 case set:

```powershell
python scripts/ingest_kaggle.py path\to\twcs.csv --limit 5000
python scripts/build_golden_template.py data\apple_support_sample.csv --size 180
```

Label the output using [the annotation guide](data/ANNOTATION_GUIDE.md), rename it to `data/golden_set.csv`, then rerun the offline commands. The ingestion command finds outbound `AppleSupport` replies and retains their inbound parent tweets; it does not incorrectly assume inbound customers have the AppleSupport author ID. The Kaggle source is excluded from git because it is large and externally distributed.

Do not submit the checked-in demo fixture as the golden set. The final CSV must retain the template's `tweet_id`, `historical_reply`, and `label_notes` columns as evidence of source sampling and manual labelling. Once the real set is ready, create a blinded review sheet, collect labels from an independent reviewer, generate LLM scores, and validate the submission evidence:

```powershell
python scripts/create_agreement_template.py --input data\golden_set.csv
# Give data\agreement_human_template.csv to an independent reviewer. They fill only human_* columns.
python scripts/judge_replies.py --input data\golden_set.csv
python scripts/merge_agreement_scores.py
python scripts/kappa.py data\agreement_scores.csv --human human_grounded --judge judge_grounded
python scripts/kappa.py data\agreement_scores.csv --human human_relevant --judge judge_relevant
python scripts/kappa.py data\agreement_scores.csv --human human_safe --judge judge_safe
python scripts/kappa.py data\agreement_scores.csv --human human_escalation_appropriate --judge judge_escalation_appropriate
python scripts/validate_submission.py
```

## Evaluation design

The majority baseline always predicts the largest intent class. The simple baseline stops on the first matching keyword. The agent uses weighted lexical scoring, security precedence, retrieval, drafting, and escalation. All agent evaluation uses leave-one-out retrieval, so a case's own human-written resolution cannot be returned while scoring it.

`LLM_JUDGE_RUBRIC.md` defines binary scores for grounded, relevant, safe, and escalation-appropriate. To run it with an API key:

```powershell
$env:OPENAI_API_KEY = "..."
python scripts/judge_replies.py --input data\golden_set.csv
```

It writes `data/llm_judge_scores.csv`. The runner uses the OpenAI Responses API's JSON-object output mode; see the [official API quickstart](https://platform.openai.com/docs/quickstart) for API setup. An independent reviewer must blind-score a stratified sample of 30 cases before seeing the judge scores. Merge their 0/1 labels with the judge score for each dimension and run, for example:

```powershell
python scripts/kappa.py data\agreement_grounded.csv --human human --judge judge
```

Report both raw agreement and Cohen's kappa for every rubric dimension. The repository contains the workflow but cannot honestly manufacture independent human-agreement evidence; collect it before submitting.

## Report

### Problem framing

For Apple Support, good means routing a customer to the right resolution family, providing a short public-safe draft grounded in prior responses, and avoiding unsafe automation. The prototype deliberately does not perform identity verification, refunds, payment changes, private-message execution, multilingual support, or full conversation-state tracking. Security, safety, legal-risk, and ambiguous cases escalate.

### Results versus baselines

After manually labelling the source-derived golden set, report agent, first-keyword baseline, and majority-baseline intent accuracy from `scripts/evaluate.py`, plus escalation accuracy and all four LLM-judge dimensions. Do not tune against the final held-out golden set.

### Top five failure modes

1. Overlapping account and security wording can conceal a compromised account.
2. Unseen paraphrases, typos, and slang defeat lexical matching.
3. A single-label router cannot fully represent messages with both delivery and refund needs.
4. Tweets often omit account/order context, so even a correct draft cannot complete resolution publicly.
5. Escalation thresholds can over-route vague cases or under-specify the right human queue.

### What is misleading about my headline number?

The bundled fixture result is not production accuracy: it is synthetic, English-only, vocabulary-aligned, and lacks a temporal split, thread-level leakage audit, adversarial noise, and independent annotator agreement. The retrieval-grounding rate only proves a returned draft exists in the leave-one-out evidence pool; it does not prove factual correctness. Use it as a reproducibility smoke test, not evidence the system can safely handle live customers.

### What I would do with one more week

I would sample complete threads, introduce a two-reviewer annotation guide, measure agreement, use a compact embedding/fine-tuned classifier, audit retrieval precision, add a temporal holdout, and red-team social-engineering cases with a support specialist.

## Decision log

See `DECISIONS.md` for the non-obvious implementation decisions and rationale.
