# API Model Policy

Canonical C-Bench requires probability scores for the supplied target sequence.
The evaluator needs target-token log probabilities for:

```text
P(target_token_i | context, previous_target_tokens)
```

Eligible access tiers:

- `open-local-logits`
- `hosted-target-logprobs`
- `hosted-echo-prompt-logprobs`, if fixture-verified
- `provider-audited-internal`, with explicit audit caveats

Non-canonical tiers:

- `generated-logprobs-only`
- `black-box-chat-only`

Generated-token logprobs are not enough because they score text the model chose
to emit, not the exact hidden target continuation. Such systems may be evaluated
in an approximate behavioral track, but not in exact C-Bench.
