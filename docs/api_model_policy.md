# API Model Policy

The C-Bench API Track is the only leaderboard track. It supports black-box
models because scoring requires a selected continuation, not internal logits.

Required run controls:

- exactly four candidates per case;
- one integer choice from 0 through 3;
- tools, browsing, retrieval, and memory disabled;
- model snapshot and provider recorded;
- reasoning effort recorded as a separate setting;
- raw predictions retained for verification.

Missing answers count as incorrect. Unknown case IDs, duplicate predictions,
and out-of-range choices invalidate a submission.

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
