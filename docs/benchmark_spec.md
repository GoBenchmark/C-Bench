# C-Bench Benchmark Spec

C-Bench measures how closely a language model predicts the true continuation
of unseen data. The public ranking metric is C-Bench Score.

## Generation Track

Each case contains:

- a context;
- a hidden target continuation;
- a domain label.

The evaluator gives only the context to the model and disables tools, retrieval,
memory, and browsing. The model returns a continuation of the requested length.

Similarity is `difflib.SequenceMatcher` ratio over the target and prediction's
UTF-8 bytes. It is calculated separately for each domain so every domain has
equal weight:

```text
Macro Similarity = mean(domain mean similarity)
```

The main score measures decimal orders of mismatch reduction:

```text
C-Bench Score =
    100 * min(1, log10(1 / (1 - Macro Similarity)) / 3)
```

Perfect similarity is defined as 100. The scale anchors are:

- 0% similarity = 0 points
- 90% similarity = 33.3 points
- 99% similarity = 66.7 points
- 99.9% similarity = 100 points

Missing continuations receive zero similarity. Duplicate IDs, unknown IDs, and
malformed records invalidate the submission. Reports include macro and micro
similarity, exact-prefix fraction, exact-match rate, domain results, and a 95%
bootstrap confidence interval.

Different model snapshots, reasoning-effort settings, tool settings, and
prompt templates are separate entries.

## API Choice Diagnostics

The repository retains four-choice continuation scoring for black-box
experiments. Its chance-adjusted API Score and accuracy are supporting
diagnostics and are not included in the Official or Public Leaderboard.

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

Official cases use private, rotating source material and fixed context and
target lengths. The target must immediately follow the context without gaps or
normalization. The released `public_dev` generation cases verify the scorer.
They are public, assumed contaminated, and not official leaderboard material.
