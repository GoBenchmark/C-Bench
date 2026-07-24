# API Model Policy

The C-Bench Generation Track is the leaderboard track. It supports black-box
models because scoring requires generated text, not internal logits. The
four-choice API Track remains an unranked diagnostic.

Required run controls:

- a fixed context and requested continuation length;
- generated continuation text;
- tools, browsing, retrieval, and memory disabled;
- model snapshot and provider recorded;
- reasoning effort recorded as a separate setting;
- raw predictions retained for verification.

Missing continuations receive zero similarity. Unknown case IDs and duplicate
predictions invalidate a submission.

## Exact Compression

Exact compression diagnostics remain available when an evaluator can obtain:

```text
P(target_token_i | context, previous_target_tokens)
```

Eligible exact access tiers include local logits, hosted target logprobs,
verified echo-prompt logprobs, and provider-audited internal scoring.

Generated-output logprobs are insufficient because they describe text chosen by
the model rather than the supplied target. Exact BPB results are retained for
research and auditing but are never placed in a leaderboard.
