# Public Dev Suite

`public_dev` is a small, reproducible development suite with one document from
each C-Bench domain: prose, multilingual text, code, and structured data. The
four files are included in this repository so users can reproduce an end-to-end
run locally.

The suite is public and assumed contaminated. It is for implementation checks,
model debugging, and transparent development results. It is not the primary
leaderboard set.

## Validate

```bash
cbench validate --suite configs/public_dev.yaml
```

## Run Baselines

```bash
cbench baseline \
  --suite configs/public_dev.yaml \
  --compressors gzip,xz \
  --output runs/public_dev_baselines.json
```

Official evaluation sets are private and are not released in this repository.
Use `public_dev` for implementation checks, model debugging, and local
comparison only.
