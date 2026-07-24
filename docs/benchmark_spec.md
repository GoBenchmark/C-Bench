# C-Bench Benchmark Spec

C-Bench measures whether a language model can identify the true continuation
of unseen data. The public ranking metric is the C-Bench API Score.

## API Track

Each case contains:

- a context;
- four same-domain candidate continuations;
- exactly one true continuation;
- a hidden answer index.

The evaluator randomizes candidate order and disables tools, retrieval, memory,
and browsing. A model returns one integer choice from 0 through 3.

Accuracy is calculated separately for each domain. Macro accuracy gives every
domain equal weight:

```text
Macro Accuracy = mean(domain accuracy)
```

The leaderboard score removes the 25% random-guessing baseline:

```text
C-Bench API Score =
    clip(100 * (Macro Accuracy - 0.25) / 0.75, 0, 100)
```

The anchors are:

- 25% macro accuracy = 0 points: random guessing
- 62.5% macro accuracy = 50 points
- 100% macro accuracy = 100 points

Missing choices count as incorrect. Duplicate IDs, unknown IDs, malformed
records, and out-of-range choices invalidate the submission. Reports include
macro and micro accuracy, correct and answered counts, domain results, and a
95% bootstrap confidence interval.

Different model snapshots, reasoning-effort settings, tool settings, and
prompt templates are separate entries.

## Exact Compression Diagnostics

The repository retains exact predictive-compression scoring for models that
expose target-token probabilities:

```text
bits = -sum(log2 P_model(target_token_i | context, previous_target_tokens))
BPB = bits / len(target_utf8_bytes)
```

Macro BPB, Micro BPB, and compressor baselines remain useful research and audit
metrics. They are not included in the Official or Public Leaderboard.

Generated-token log probabilities cannot replace target-token probabilities.
They score text selected by the model, not the supplied benchmark target.

## Case Construction

Official cases use private, rotating source material. Distractors must:

- match the true continuation's domain, format, and approximate length;
- remain locally plausible after the context;
- avoid obvious answer-only artifacts;
- be permuted independently for each run;
- pass duplicate and accidental-answer checks.

The released `public_dev` API cases verify the scorer and submission format.
They are public, assumed contaminated, and not official leaderboard material.
