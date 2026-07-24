# MDL / Artifact Track

The predictive track does not count model size. The future MDL track asks which
full system gives the shortest total description of the data:

```text
MDL bits = data bits + alpha * artifact bits
```

Artifacts include weights, tokenizer files, dictionaries, decompressor code,
configuration, and required runtime files.

Possible variants:

- Artifact-capped: fixed caps such as 16 MB, 128 MB, or 1 GB.
- Artifact-amortized: model size divided across a fixed evaluation corpus size.
- Unlimited artifact: reported separately, not the main leaderboard.

The MDL track should run in a sandbox with network disabled and private data
mounted read-only.
