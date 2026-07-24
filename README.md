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

C-Bench averages BPB across domains, reports reproducible metadata, and uses
hidden evaluation data to measure generalization rather than memorization.

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
