# Public Dev Suite

`public_dev` is a small, reproducible development suite with one document from
each C-Bench domain: prose, multilingual text, code, and structured data. The
four files are included in this repository so users can reproduce an end-to-end
run locally.

The suite is public and assumed contaminated. It is for implementation checks,
model debugging, and transparent development results. It is not the primary
leaderboard set.

The repository includes `datasets/public_dev_generation_cases.jsonl`, containing
one context and target per domain. These cases verify continuation scoring and
reports. Rebuild them deterministically with:

```bash
python scripts/build_public_generation_cases.py
```

Score a prediction file with:

```bash
cbench generation-score \
  --cases datasets/public_dev_generation_cases.jsonl \
  --predictions datasets/public_dev_generation_predictions.example.jsonl \
  --suite public_dev_generation \
  --model example-model \
  --output runs/example-generation-score.json
```

Four-choice API cases and `cbench api-score` remain available as unranked
diagnostics.

## Validate

```bash
cbench validate --suite configs/public_dev.yaml
```

## Exact Diagnostic Baselines

```bash
cbench baseline \
  --suite configs/public_dev.yaml \
  --compressors gzip,xz \
  --output runs/public_dev_baselines.json
```

Official evaluation sets are private and are not released in this repository.
Use `public_dev` for implementation checks, model debugging, and local
comparison only.
