# C-Bench Benchmark Spec

C-Bench measures language models as predictive compressors. For a target byte
string represented as native model tokens, the score is:

```text
bits = -sum(log2 P_model(target_token_i | context, previous_target_tokens))
BPB = bits / len(target_utf8_bytes)
```

Lower BPB is better. Raw uncompressed bytes are 8 BPB.

## Public Leaderboard Score

The headline leaderboard score is **C-Bench Score**, a fixed 0-100 linear
conversion of Macro BPB where higher is better:

```text
C-Bench Score = clip(100 * (1 - Macro BPB / 16), 0, 100)
```

The published anchors are:

- 0 BPB = 100 points: theoretical perfect prediction
- 8 BPB = 50 points: raw uncompressed bytes
- 16 BPB = 0 points: twice the raw-byte cost

The 16 BPB lower anchor gives inefficient models and compressors room below the
raw baseline. Because the conversion is monotonic, ranking by C-Bench Score is
identical to ranking by Macro BPB. BPB must remain in every report for audit and
cross-benchmark comparison.

The primary implementation uses each model's native tokenizer, then normalizes
by raw UTF-8 target bytes. Token perplexity is not a cross-model metric and must
not be used as the leaderboard score.

## Tracks

- Predictive Compression: model size is excluded; score is ideal code length.
- Conditional Compression: context is provided for free; only target bytes count.
- Efficiency-aware Reporting: BPB is reported with time, memory, and cost.
- Reasoning-assisted Compression: reasoning-effort settings are separate entries.
- MDL / Artifact Compression: future track that also counts model/decompressor artifacts.

All public leaderboard tables should show C-Bench Score first, followed by
Macro BPB, Micro BPB, domain scores, and the confidence interval.

## Public Fixture Warning

The bundled `dev_small` suite exists only to verify code paths, byte counting,
and reporting. It is not contamination-safe and must not be treated as a real
leaderboard.

The reproducible `public_dev` suite provides one larger document per domain for
public debugging. Official leaderboard evaluation uses a separate private,
rotating suite that is not released in this repository.
