# Decision log

1. **Brand: AppleSupport.** It has a recognizable public support voice and enough recurring issue families to support intent discovery.
2. **Seven intents.** The set is small enough to label consistently while preserving materially different support actions.
3. **No Banking77 labels.** Banking77 is useful for intent experiments but would introduce a domain mismatch for Apple replies.
4. **Python standard library only.** The headline run must be reproducible in a clean environment in under 15 minutes.
5. **Transparent lexical classifier.** Its evidence terms make live explanation and failure analysis straightforward.
6. **Security precedence.** Security signals override overlapping account-access terms because the cost of unsafe automation is high.
7. **Retrieval before drafting.** Replies reuse resolutions from similar labeled cases rather than inventing policy.
8. **No public secrets.** Drafts never ask for passwords, codes, or card numbers; sensitive cases escalate.
9. **Seven-way majority baseline.** It is intentionally weak but exposes class imbalance and makes the 0.20 score interpretable.
10. **Curated 150-case golden set.** It gives a stable offline contract while the multi-million-row source remains optional.
11. **Exact-match intent metric.** It is strict, easy to reproduce, and exposes multi-intent limitations rather than hiding them in a soft score.
12. **Deterministic judge rubric.** It provides an executable starting point, but the report explicitly says independent human calibration is still required.
