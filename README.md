# C-Bench Reference Implementation

![C-Bench predictive compression](docs/assets/cbench-predictive-compression.png)

## Philosophy

C-Bench is built around a simple question: **how many bits does a model need to
describe unfamiliar data?** A model that assigns high probability to the actual
next content can encode it compactly; a surprised model needs more bits. This
turns language-model evaluation into a measurable test of prediction,
calibration, and generalization.

The benchmark follows these principles:

- **Measure predictions, not performances.** C-Bench scores the probability of
  a supplied target sequence. It does not ask a model to generate an answer and
  then judge the answer's style or similarity.
- **Normalize across tokenizers.** Models use their native tokenization, while
  the final cost is normalized by the target's raw UTF-8 bytes. Token count and
  vocabulary design should not decide the ranking.
- **Reward broad understanding.** Macro BPB gives each domain equal weight so
  an easy, large slice cannot hide weak performance elsewhere.
- **Make every number auditable.** Scores should include the suite, model
  identity, inference settings, access tier, confidence interval, and enough
  metadata to reproduce the run.
- **Separate capability from resources.** Predictive compression, reasoning
  effort, latency, cost, and model or artifact size are related but different
  questions. They belong in separate tracks or clearly labeled columns.
- **Treat leakage as a first-class risk.** Public development data makes the
  implementation inspectable; serious leaderboard claims require hidden or
  rotating evaluation data and strict submission procedures.

The goal is not to crown a model that memorizes a fixed collection. It is to
build a durable measurement of how efficiently models represent data they have
not been allowed to inspect in advance.

C-Bench evaluates language models as predictive compressors. The public
leaderboard score is a fixed 0-100 linear conversion of Macro BPB, where higher
is better. BPB remains the underlying audit metric and is lower-is-better.

The score anchors are 0 BPB = 100, raw bytes at 8 BPB = 50, and 16 BPB = 0.

This repository is a small reference implementation. It releases only the
`public_dev` suite so people can install C-Bench, test the implementation, and
run their own models. Public data is assumed contaminated and is not a serious
leaderboard set.

Official evaluation sets are private and are not included in this repository.
They are reserved for maintainer-controlled, contamination-resistant
leaderboard evaluations. See `docs/public_dev.md` and
`docs/contamination_policy.md`.

## Leaderboards

The headline ranking metric is C-Bench Score, a 0-100 scale derived from Macro
BPB. Higher is better. An official model entry requires an exact score for the
supplied target tokens and a reproducible private evaluation run.

### Official C-Bench leaderboard

Official test data is private and is not published in this repository. The
following rows record maintainer runs on that private suite. The API returned
generated continuations but not supplied-target token probabilities, so exact
C-Bench Score and Macro BPB are intentionally left blank. Continuation
similarity is shown for traceability only and does not determine the ranking.

| Rank | Model | Access / setting | Suite | C-Bench Score | Macro BPB | Official run signal | Notes |
|---:|---|---|---|---:|---:|---|---|
| - | gpt-5.6-terra | OpenAI API / xhigh | official_v1 | - | - | 0.092 similarity; 0/12 exact | private official run; not BPB-ranked |
| - | gpt-5.6-sol | OpenAI API / xhigh | official_v1 | - | - | 0.044 similarity; 0/12 exact | private official run; not BPB-ranked |
| - | gpt-5.6-luna | OpenAI API / xhigh | official_v1 | - | - | 0.000 similarity; 0/12 exact | private official run; not BPB-ranked |

### Public Leaderboard

This table contains reproducible community submissions evaluated on released
public suites. Public results remain separate from private official evaluations.
Each submission should include the model identity, suite, settings, exactness
metadata, and a verifiable report.

| Rank | Model | Submitted by | Suite | C-Bench Score | Macro BPB | Evidence | Status |
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

### 4. Run C-Bench

Run the built-in classical baselines first:

```bash
cbench baseline \
  --suite configs/public_dev.yaml \
  --compressors gzip,xz \
  --output runs/baselines.json
```

This writes the raw results to `runs/baselines.json`. Generate a readable
Markdown report with:

```bash
cbench report \
  --inputs runs/baselines.json \
  --output reports/public_dev_report.md
```

The report shows C-Bench Score, Macro BPB, Micro BPB, confidence intervals, and
the score for each domain.

### Optional model scoring

Install the Hugging Face dependencies, then score a causal language model:

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

## Exactness Policy

Canonical C-Bench requires target-token probabilities for the supplied target
sequence. APIs that only return logprobs for generated text are approximate and
must not be reported as exact compression scores.
