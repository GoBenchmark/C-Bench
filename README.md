# C-Bench: Measuring Language Models Through Compression

![C-Bench predictive compression](docs/assets/cbench-predictive-compression.png)

## Principle

**Compression and prediction are deeply equivalent. A better language model is
a better general-purpose predictive compressor.**

For a sequence of tokens, an autoregressive model defines

```math
P_\theta(x) = \prod_{t=1}^{T} P_\theta(x_t \mid x_1,\ldots,x_{t-1})
```

By source coding, its ideal lossless code length and normalized cost are

```math
L_\theta(x) = -\log_2 P_\theta(x)
            = -\sum_{t=1}^{T}\log_2 P_\theta(x_t \mid x_1,\ldots,x_{t-1})
```

```math
\mathrm{BPB}(x) = \frac{L_\theta(x)}{\lvert x\rvert_{\mathrm{bytes}}}
```

Better prediction means fewer bits.

C-Bench applies this principle through a black-box predictive-choice test. For
each hidden context, a model selects the true next passage from four
same-domain candidates. Candidate order is randomized and tools and retrieval
are disabled.

If $A$ is mean accuracy across domains, the leaderboard score is

```math
\mathrm{C\text{-}Bench\ API\ Score}
=100\min\left(1,\max\left(0,\frac{A-0.25}{0.75}\right)\right).
```

Random guessing scores 0, perfect prediction scores 100, and higher is better.
The exact BPB implementation remains available for compression research, but
exact results are not shown in either leaderboard.

This repository is a small reference implementation. It releases only the
`public_dev` suite so people can install C-Bench, test the implementation, and
run their own models. Public data is assumed contaminated and is not a serious
leaderboard set.

Official evaluation sets are private and are not included in this repository.
They are reserved for maintainer-controlled, contamination-resistant
leaderboard evaluations. See `docs/public_dev.md` and
`docs/contamination_policy.md`.

## Leaderboards

The only ranking metric is **C-Bench API Score**, a chance-adjusted 0-100
predictive-choice score. Different reasoning-effort settings are separate
entries. Continuation similarity and exact BPB results are not leaderboard
metrics.

### Official C-Bench API Leaderboard

Official cases and answer keys are private and are not published in this
repository. Maintainer-controlled runs use hidden, rotating cases. The archived
entries below were completed before the four-choice API Track protocol was
adopted. Their saved continuation evidence is retained, but it cannot be
converted into C-Bench API Score and does not determine rank.

| Rank | Model | Access / setting | Suite | C-Bench API Score | Macro accuracy | Evidence | Status |
|---:|---|---|---|---:|---:|---|---|
| - | gpt-5.6-sol | OpenAI API / xhigh | official_v1 | - | - | 12/12 completed; 0.866 continuation similarity | Archived pre-API Track run |
| - | gpt-5.6-luna | OpenAI API / xhigh | official_v1 | - | - | 12/12 completed; 0.747 continuation similarity | Archived pre-API Track run |
| - | gpt-5.6-terra | OpenAI API / xhigh | official_v1 | - | - | 12/12 completed; 0.722 continuation similarity | Archived pre-API Track run |

### Public Leaderboard

This table contains reproducible community submissions evaluated on released
public suites. Public results remain separate from private official evaluations.
Each submission should include the model identity, suite, reasoning and tool
settings, raw choices, and a verifiable report.

| Rank | Model | Submitted by | Suite | C-Bench API Score | Macro accuracy | Evidence | Status |
|---:|---|---|---|---:|---:|---|---|
| - | No validated submissions yet | - | - | - | - | - | Open for submissions |

## Install

Requirements: Python 3.10 or newer.

### 1. Get the code

```bash
git clone https://github.com/GoBenchmark/C-Bench.git
cd C-Bench
```

If you already have the repository, just open a terminal in its directory.

### 2. Create an environment and install C-Bench

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

### 3. Check the installation

```bash
cbench validate --suite configs/public_dev.yaml
```

You should see `Validated 4 entries for suite public_dev`.

### 4. Create model predictions

The released API development cases are in
`datasets/public_dev_api_cases.jsonl`. Give each case's `context` and four
numbered `candidates` to a model, then save one choice per line:

```json
{"id":"public_dev_prose_001","choice":3}
```

Use zero-based choices from 0 through 3. A complete example prediction file is
included to verify the command; it is not a model result.

### 5. Calculate the C-Bench API Score

```bash
cbench api-score \
  --cases datasets/public_dev_api_cases.jsonl \
  --predictions datasets/public_dev_api_predictions.example.jsonl \
  --suite public_dev_api \
  --model example-model \
  --reasoning-effort medium \
  --output runs/example-api-score.json
```

Generate a readable leaderboard report:

```bash
cbench report \
  --inputs runs/example-api-score.json \
  --output reports/public_dev_api_report.md
```

The report shows C-Bench API Score, its confidence interval, macro accuracy,
correct choices, and domain results.

### Optional exact compression diagnostics

Exact BPB scoring remains available for open-weight causal language models. It
is retained for research and auditing and does not produce a leaderboard entry.

```bash
python -m pip install -e '.[hf]'
```

```bash
cbench score \
  --model hf:gpt2 \
  --suite configs/public_dev.yaml \
  --max-context-tokens 1024 \
  --target-chunk-tokens 256 \
  --output runs/gpt2.json
```

Optional compressor packages can be installed with:

```bash
python -m pip install -e '.[zstd,brotli]'
```

## Submission Policy

Leaderboard submissions must include the model identity, reasoning effort,
suite version, raw choice file, generated report, and tools/retrieval settings.
Official submissions are rescored against private cases. Public development
scores are kept in the Public Leaderboard and cannot become official results.
