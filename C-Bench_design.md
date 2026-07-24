# C-Bench: A Serious Design for an LLM-as-Compressor Benchmark

**Version:** 0.3 design
**Date:** 2026-07-24
**Purpose:** Define a predictive benchmark whose public leaderboard works with
black-box model APIs while retaining exact compression diagnostics for models
that expose target probabilities.

---

## 0. Executive summary

**C-Bench** is a benchmark for measuring how well language models predict, and therefore compress, unseen data.

The leaderboard uses a hidden four-choice continuation task. Its
chance-adjusted 0-100 score measures whether a model identifies the true next
passage more often than random guessing.

The implementation has two evaluation paths:

1. **API Track** — the only ranked track; supports black-box model APIs.
2. **Exact Compression Diagnostics** — measures BPB when target-token
   probabilities are available; retained for research but not ranked.

The benchmark should also explicitly separate **pure probability scoring** from **reasoning-assisted / test-time-compute scoring**. A reasoning model run at `medium` effort and the same model run at `xhigh` effort should not silently share one leaderboard entry, because extra inference-time compute may change conditional predictions, cost, latency, and reproducibility.

Exact compression diagnostics require local/open logits or a provider API that
can score a supplied target continuation. Generated-token logprobs are not
sufficient for BPB, but black-box APIs can participate in the API Track.

A serious implementation should begin with open-weight model scoring and public development data, then move to a private, contamination-resistant evaluation server for leaderboard results.

---

## 1. Motivation

Many NLP benchmarks evaluate narrow behaviors: answering exam questions, generating code, classifying sentiment, or following instructions. A compression benchmark asks a more primitive question:

> How many bits does the model need to describe reality-like data?

The benchmark is grounded in the prediction-compression equivalence:

\[
L(x) = -\sum_i \log_2 P_\theta(s_i \mid s_{<i})
\]

where \(s_i\) is the next symbol, token, byte, character, or segment being encoded.

If a model gives high probability to the correct next symbols, it gives the data a short code. If it is surprised, the code length is long.

The goal is not to replace all benchmarks. The goal is to produce a **continuous, calibrated, tokenizer-aware, contamination-resistant measure of predictive understanding**.

---

## 2. Prior art and constraints

C-Bench is not invented in a vacuum.

Relevant precedents:

- **Language Modeling Is Compression**: predictive models can be transformed into lossless compressors and vice versa; the paper evaluates foundation models through the compression lens.  
  Source: https://arxiv.org/abs/2309.10668

- **Ranking LLMs by Compression**: proposes ranking LLMs by compression ratio derived from cumulative negative log-probabilities, without necessarily running a physical arithmetic coder.  
  Source: https://arxiv.org/abs/2406.14171

- **OpenAI Parameter Golf**: a practical challenge using tokenizer-agnostic bits per byte on FineWeb validation under strong artifact and compute constraints.  
  Source: https://github.com/openai/parameter-golf

- **Large Text Compression Benchmark / Hutter-style benchmarks**: rank systems by compressed file size plus decompressor/runtime artifacts, making model/decompressor size part of the score.  
  Source: https://www.mattmahoney.net/dc/textrules.html

- **gzip + kNN text classification**: demonstrates that even simple compressors capture useful text similarity signals, especially in low-resource and OOD classification settings.  
  Source: https://aclanthology.org/2023.findings-acl.426/

C-Bench should borrow the rigor of compression benchmarks, but use modern LLM probability scoring where exact decompression artifacts are impractical or unavailable.

---

## 3. Benchmark goals

### 3.1 Primary goals

C-Bench should measure:

1. **Predictive quality**: How efficiently can a model encode held-out data?
2. **Calibration**: Does the model place probability mass on the actual continuation?
3. **Context use**: How much does longer context improve compression?
4. **Cross-domain generality**: Does compression transfer across prose, code, science, multilingual text, structured data, and conditional tasks?
5. **Efficiency tradeoffs**: What compression quality is achieved per unit cost, latency, memory, and model size?

### 3.2 Non-goals

C-Bench should not try to be:

- a replacement for human preference evaluation;
- a benchmark of conversational helpfulness;
- a benchmark of tool use;
- a benchmark of safety behavior;
- a pure memorization contest;
- a public static dataset that frontier models can train on.

---

## 4. Core score

### 4.1 Predictive bits

For a target byte string \(y\), represented internally as a sequence of model-native tokens \(t_1, \dots, t_n\):

\[
\text{bits}(y \mid c) = -\sum_{i=1}^n \log_2 P_\theta(t_i \mid c, t_{<i})
\]

where \(c\) is optional context.

### 4.2 Bits per byte

The primary model-comparable metric is:

\[
\text{BPB} = \frac{\text{bits}(y \mid c)}{|y|_{\text{UTF-8 bytes}}}
\]

Lower is better.

Raw uncompressed bytes have:

\[
\text{BPB}_{\text{raw}} = 8
\]

A compression ratio against raw bytes is:

\[
\text{CR}_{\text{raw}} = \frac{\text{BPB}}{8}
\]

### 4.3 Relative gain over classical compressors

Report classical compressor baselines on the same byte stream:

- gzip
- zstd
- brotli
- xz/lzma
- optional stronger context-mixing compressors if licensing and runtime allow

A useful normalized comparison is:

\[
\Delta_{\text{zstd}} = \frac{\text{BPB}_{\text{zstd}} - \text{BPB}_{\text{model}}}{\text{BPB}_{\text{zstd}}}
\]

Positive means the model beats zstd on that slice.

### 4.4 Macro vs micro averaging

Report both:

- **Micro BPB**: aggregate all bits and bytes across the entire suite.
- **Macro BPB**: average BPB across domains, giving each domain equal weight.

BPB results are exact compression diagnostics and are not placed in the
leaderboard.

### 4.5 Public API Track score

Each case has four candidate continuations. Let \(A\) be mean accuracy across
domains. The leaderboard score is:

\[
\text{C-Bench API Score}
= \operatorname{clip}\left(100\frac{A-0.25}{0.75}, 0, 100\right)
\]

Random guessing scores 0, 62.5% macro accuracy scores 50, and perfect prediction
scores 100.

### 4.6 Confidence intervals

Report 95% bootstrap confidence intervals over documents, not over individual tokens. This makes the uncertainty reflect document-level variation rather than token count illusion.

---

## 5. Tracks

### Track A: Predictive Compression

**Question:** Which model best predicts unseen data?

- Model size is excluded.
- Score is ideal code length from negative log-probability.
- No actual compressed artifact required.
- Best for comparing frontier predictive capability.

Primary metric:

\[
\text{BPB}_{\text{predictive}}
\]

### Track B: MDL / Artifact Compression

**Question:** Which full system gives the shortest total description of the data?

Inspired by classical compression benchmarks that count the compressed file plus the decompressor/runtime files.

Score:

\[
\text{MDL bits} = \text{data bits} + \alpha \cdot \text{artifact bits}
\]

where the artifact includes model weights, tokenizer, decompressor, dictionaries, config files, and required runtime files.

Practical variants:

1. **Artifact-capped track**: e.g. 16 MB, 128 MB, 1 GB caps.
2. **Artifact-amortized track**: model size divided across a fixed evaluation corpus size.
3. **Unlimited artifact track**: reported as an unranked diagnostic.

### Track C: Conditional Compression

**Question:** How efficiently does a model encode a target given side information?

Score:

\[
L(y \mid c) = -\sum_i \log_2 P_\theta(y_i \mid c, y_{<i})
\]

Examples:

| Task type | Context \(c\) | Target \(y\) |
|---|---|---|
| QA | question + evidence | answer |
| Translation | source sentence | target sentence |
| Classification | document | label |
| Code | specification + tests | reference solution or patch |
| Scientific reasoning | problem statement | derivation or final solution |
| Summarization | document | human summary |

Conditional compression is where C-Bench becomes more than next-token prediction. It turns many tasks into one probabilistic scoring law.

### Track D: Efficiency-aware Compression

Report predictive BPB alongside:

- wall-clock scoring time;
- tokens/s or bytes/s;
- peak VRAM/RAM;
- estimated energy;
- dollar cost for API models;
- context length used.

Primary ranking uses the C-Bench API Score. Reasoning tokens, latency, and cost
are companion columns unless a separate efficiency track is created. BPB
efficiency remains available only for exact diagnostics.

### Track E: Test-Time Compute / Reasoning-Assisted Compression

**Question:** Does extra inference-time reasoning improve compression, and where?

This track is for reasoning models whose APIs expose a control such as
`reasoning_effort`, `thinking_budget`, or `reasoning_tokens`.

Policy:

- Each API Track entry uses one fixed, documented setting.
- Variable reasoning effort must be reported as separate entries, e.g. `model/medium`, `model/high`, `model/xhigh`.
- The leaderboard should report reasoning tokens, latency, and cost when available.
- Exact BPB diagnostics remain separate and unranked.

Expected behavior:

| Suite type | Likely effect of higher reasoning effort |
|---|---:|
| raw prose continuation | small or negligible |
| code continuation | small to moderate |
| math/proof continuation | moderate possible |
| conditional QA / science reasoning | moderate to large possible |
| agentic tool-use outputs | large possible, but outside pure C-Bench unless tools are explicitly allowed |

This track can reveal whether extra inference-time compute helps **semantic compression** more than **surface continuation compression**.

---

## 6. Evaluation suites

C-Bench should be organized into suites, each with public development data and private held-out data.

### 6.1 Core text suite

Purpose: measure general language modeling and world-text prediction.

Domains:

- contemporary web text;
- essays and blogs;
- news-like articles from licensed or newly collected sources;
- educational material;
- domain-specific prose.

Risks:

- public web data is likely contaminated;
- copyrighted material may be legally complex;
- model providers may have trained on current public sources.

Mitigation:

- use private, licensed, or newly commissioned content;
- use rolling windows collected after model snapshot freeze when possible;
- deduplicate against known public corpora;
- keep final test shards private.

### 6.2 Scientific and technical suite

Purpose: measure specialized predictive structure.

Domains:

- physics, biology, medicine, chemistry, and CS excerpts;
- new paper abstracts and introductions;
- theorem/proof-like text;
- lab-protocol-like structured prose.

Mitigation:

- include a public dev set from permissively licensed sources;
- private eval should use recently written or licensed materials.

### 6.3 Code and formal structure suite

Purpose: measure syntax, long-range dependency, and symbolic regularity.

Domains:

- Python, Rust, TypeScript, C++;
- config files;
- JSON, YAML, TOML;
- SQL;
- unit-test-driven patch targets.

Mitigation:

- use permissively licensed repositories only;
- for hidden data, commission small private repos or generate deterministic code tasks by humans;
- preserve exact bytes, including whitespace.

### 6.4 Multilingual suite

Purpose: prevent the benchmark from becoming English-tokenizer-specific.

Languages should include:

- high-resource Latin-script languages;
- Chinese and Japanese;
- Arabic or Hebrew;
- Hindi or other Indic scripts;
- lower-resource languages where licensing permits.

Metric remains BPB, not token perplexity.

### 6.5 Structured data suite

Purpose: evaluate pattern induction beyond prose.

Domains:

- logs;
- CSV-like records;
- JSON event streams;
- synthetic but semantically meaningful tables;
- schema-constrained data.

This suite is valuable because classical compressors may perform strongly here; models should not receive easy credit for surface text alone.

### 6.6 Conditional suite

Purpose: unify classical NLP tasks under compression.

Candidate tasks:

- document → label;
- question + passage → answer;
- source sentence → translation;
- spec → code patch;
- paper intro → abstract conclusion;
- partial theorem statement → proof step.

Use carefully constrained target spaces for labels and short answers where exact probability scoring is possible.

---

## 7. Context regimes

Context length changes compression quality, so context budget must be explicit.

Recommended leaderboard variants:

| Regime | Maximum available context | Purpose |
|---|---:|---|
| C-Bench-S | 8 KiB of prior bytes or equivalent tokens | small-context fairness |
| C-Bench-M | 128 KiB | practical long context |
| C-Bench-L | 1 MiB | long-context systems |
| C-Bench-Native | model’s native maximum | frontier capability, less fair |

For streaming compression, prior bytes from the same document may be used as context. Document boundaries reset context.

For conditional compression, the side information \(c\) is free context; only the target \(y\) counts toward BPB.

---

## 8. Tokenization policy

Tokenizer differences are one of the hardest practical issues.

### 8.1 What not to do

Do not compare raw token perplexity across models. Tokenizers differ too much.

### 8.2 Baseline policy: native tokenizer, byte normalization

Each model is scored using its native tokenizer. The reported metric is normalized by raw UTF-8 target bytes.

This is not perfect, but it is practical and consistent with current LLM evaluation constraints.

### 8.3 Boundary handling

For conditional tasks:

1. Store raw `context_bytes` and `target_bytes` separately.
2. Decode to text only if the model requires text input.
3. Insert a standardized boundary delimiter when appropriate, e.g. `\n<CBENCH_TARGET>\n`, but score only target content after the delimiter.
4. Tokenize `context + delimiter + target` together.
5. Score only tokens whose byte spans are wholly inside the target region.
6. If a token crosses the boundary, use a conservative documented policy:
   - either score the whole cross-boundary token and count its target-overlap bytes;
   - or force a delimiter that prevents cross-boundary merges;
   - or use tokenizer offset mappings where available.

The recommended v1 policy is to use a delimiter that prevents most merges and to reject model/tokenizer combinations where offsets cannot be audited.

### 8.4 Byte-level ideal scoring is future work

A fully tokenizer-neutral byte-level score would require converting native-token probabilities into byte probabilities by marginalizing over all tokenizations. This is mathematically cleaner but expensive and difficult for closed models. It should be treated as a research extension, not a v1 dependency.

---

## 9. Data leakage and contamination controls

This is the make-or-break issue.

### 9.1 Threats

- Public dev/test data may have been in training sets.
- Recent public web data may still be included in post-training or retrieval systems.
- Closed API models can update silently.
- Benchmark datasets can leak through prompts or public submissions.
- A model may memorize benchmark canaries.

### 9.2 Policy

For public leaderboards:

1. Public dev set is for debugging only.
2. Private test set is never released during an active evaluation cycle.
3. Test set is refreshed periodically.
4. The eval server records model snapshot IDs, submission dates, and inference settings.
5. API models must run with tools, browsing, retrieval, and memory disabled.
6. Submissions must not receive raw private examples.
7. Human-authored private data, licensed data, or newly commissioned data should be preferred over scraped public data.

### 9.3 Canary and audit strategy

Add non-semantic canaries and near-duplicate checks:

- random high-entropy strings embedded in private documents;
- private paraphrase clusters;
- document fingerprints;
- similarity search against known public corpora;
- memorization probes after evaluation.

Do not rely on canaries alone. They detect some leaks but do not prove absence of contamination.

---

## 10. Closed-model, API, and provider-access constraints

The canonical leaderboard score is the C-Bench API Score and requires only a
valid choice among the supplied continuations. An exact BPB diagnostic requires
access to the probability assigned to the **actual supplied target sequence**,
not merely the probability of text the model happened to generate.

### 10.1 Exact scoring requirement

The model interface must expose the equivalent of:

```text
score(context, target) -> target_token_logprobs, total_logprob_target, token_count, byte_count, metadata
```

The score must correspond to:

```text
P(target_token_i | context, previous_target_tokens)
```

for every target token.

The evaluator does **not** necessarily need full logits or the full next-token distribution if the benchmark only reports ideal code length. It does need the log probability of each true target token. A real arithmetic-coded file would require a reproducible distribution interface, but the v1 benchmark can use summed negative log probabilities as the ideal code length.

### 10.2 Generated-token logprobs are not enough

Many APIs expose logprobs for generated output tokens. That is useful for confidence analysis, but it is not enough for exact C-Bench unless the API can be forced to score the hidden target continuation.

A model that cannot score supplied targets cannot answer the exact compression
question:

> How many bits would this model need to encode this exact data?

It can participate fully in the C-Bench API Track, but not in exact BPB
diagnostics.

### 10.3 Provider access tiers

C-Bench should label submissions by access tier:

| Tier | Name | Eligible for exact diagnostics? | API Track eligible? | Description |
|---|---|---:|---:|---|
| 1 | `open-local-logits` | Yes | Yes | Open-weight or locally hosted model. |
| 2 | `hosted-target-logprobs` | Yes | Yes | Provider returns supplied-target logprobs. |
| 3 | `hosted-echo-prompt-logprobs` | Yes, if verified | Yes | Verified prompt-token scoring. |
| 4 | `provider-audited-internal` | Conditional | Yes | Provider runs an internal exact scorer. |
| 5 | `generated-logprobs-only` | No | Yes | Generated-token probabilities only. |
| 6 | `black-box-chat-only` | No | Yes | Choice output without internal probabilities. |

### 10.4 Exact provider API policy

For closed models participating in exact diagnostics, the preferred API is:

```python
score(
    model="fixed-version-or-snapshot",
    context="...",
    target="...",
    settings={
        "tools": "disabled",
        "retrieval": "disabled",
        "temperature": 0,
        "reasoning_effort": "medium"
    }
) -> {
    "target_tokens": [...],
    "target_token_bytes": [...],
    "target_token_logprobs": [...],
    "total_nats": ...,
    "model_fingerprint": "..."
}
```

Important constraints:

- The endpoint must score the supplied target, not generate a new target.
- It must return enough token boundary information to map logprobs to target bytes.
- It must expose a fixed model version or fingerprint.
- It must disable tools, browsing, retrieval, and memory for exact diagnostic runs.
- It must document whether reasoning effort or hidden thinking affects scoring.

### 10.5 API capability registry

C-Bench should maintain a provider capability registry rather than hardcoding assumptions. Each provider/model entry should record:

- provider name;
- endpoint family;
- model snapshot/version;
- whether supplied-target scoring is supported;
- whether prompt-token logprobs are available;
- whether generated-token-only logprobs are available;
- maximum context length;
- tokenizer/byte information availability;
- reasoning-effort controls;
- tool/retrieval disable controls;
- date verified;
- verification script and expected fixture output.

A provider should be considered exact-scoreable only after passing small public fixture tests where the same target is scored reproducibly.

### 10.6 Closed API contamination risk

Sending private benchmark text to a provider API can leak the hidden test set through provider logging or future training. Therefore:

- public-dev data may be sent freely if licensing allows;
- private leaderboard data should use provider agreements, no-training terms, or provider-internal audited scoring;
- the benchmark should track which private shards were exposed to which providers;
- provider API results should be marked with exposure/audit metadata.

### 10.7 Black-box API Track

The ranked API Track supports chat-only models through:

- finite candidate continuation ranking;
- answer selection over a closed set.

This track is the canonical C-Bench leaderboard, but it must not be called an
exact BPB measurement. It measures predictive discrimination as a practical
black-box proxy for compression quality.

---

## 11. Reproducibility policy

For open-weight submissions, require:

- model weights hash;
- tokenizer hash;
- code commit hash;
- inference dtype;
- hardware class;
- exact package versions;
- deterministic settings when possible;
- context regime;
- max sequence length;
- BOS/EOS handling;
- prompt template if any;
- system messages if any;
- scoring script version;
- access tier;
- provider endpoint family if applicable;
- target-logprob support verification result;
- tool/retrieval/memory disable settings;
- reasoning effort or thinking-budget setting;
- hidden reasoning token accounting if available.

For floating point reproducibility, use tolerances:

- exact tokenization must match;
- total BPB should reproduce within a small tolerance, e.g. `1e-4` BPB for open-weight models under documented hardware/dtype.

---

## 12. Security model

C-Bench will eventually handle private data. Treat submitted code as hostile.

### 12.1 For open-weight artifact submissions

- Run in network-disabled containers.
- Enforce CPU/GPU/memory/time limits.
- Mount private data read-only.
- Block filesystem writes except designated output directories.
- Store only aggregate scores unless sample-level outputs are explicitly approved.
- Randomize test shard order to reduce side channels.

### 12.2 For API submissions

- The benchmark server, not the submitter, calls the model API.
- The submitter never sees private inputs.
- Provider terms must allow benchmark use.
- Logs must not expose private data to unauthorized parties.

---

## 13. Baselines

Every release should include baselines:

### 13.1 Classical compressors

- raw bytes: 8 BPB;
- gzip;
- zstd;
- brotli;
- xz/lzma.

### 13.2 Simple statistical models

- byte unigram;
- byte n-gram;
- character n-gram;
- small PPM-like model if available.

### 13.3 Neural baselines

- small open-weight transformer;
- mid-size open-weight transformer;
- long-context open-weight model;
- optional byte-level model.

Baselines should be recomputed whenever the scoring harness changes.

---

## 14. Reporting format

Each run should output a machine-readable JSON file:

```json
{
  "benchmark_version": "cbench-0.3",
  "run_type": "api_track",
  "suite": "api_private_2026q3",
  "model": {
    "name": "example/model",
    "access_tier": "black-box-chat-only",
    "provider_endpoint": "responses",
    "reasoning_effort": "medium",
    "tools": "disabled",
    "retrieval": "disabled"
  },
  "scores": {
    "cbench_api_score": 76.4,
    "macro_accuracy": 0.823,
    "micro_accuracy": 0.817,
    "chance_accuracy": 0.25,
    "candidate_count": 4,
    "correct": 817,
    "cases": 1000,
    "score_100_ci_95": [73.1, 79.6]
  },
  "resources": {
    "wall_time_seconds": 1234.5,
    "peak_vram_gb": 42.0,
    "peak_ram_gb": 64.0,
    "tokens_per_second": 1123.0,
    "estimated_cost_usd": null,
    "reasoning_tokens": null,
    "api_calls": null
  },
  "domain_breakdown": [
    {"domain": "web", "cases": 500, "correct": 420, "accuracy": 0.84},
    {"domain": "code", "cases": 500, "correct": 397, "accuracy": 0.794}
  ]
}
```

---

## 15. Scoring algorithm for open-weight models

### 15.1 Streaming text compression

For each document:

1. Load raw bytes.
2. Decode to text if the model tokenizer requires text. Preserve exact byte length for normalization.
3. Tokenize document.
4. Score left-to-right using a rolling context window.
5. Reset at document boundaries.
6. Sum `-log2 p(target_token)` for every scored target token.
7. Divide by raw byte count.

### 15.2 Pseudocode

```python
for document in suite:
    text = decode_utf8(document.bytes)
    token_ids = tokenizer.encode(text, add_special_tokens=False)

    doc_bits = 0.0
    doc_bytes = len(document.bytes)

    # Rolling log-likelihood with a context cap.
    for window in make_scoring_windows(token_ids, max_context_tokens, target_chunk_tokens):
        input_ids = window.context_ids + window.target_ids
        logits = model(input_ids).logits

        # Shift logits so logits[j] predicts input_ids[j + 1].
        target_positions = positions_corresponding_to_target_tokens(window)
        logprobs = log_softmax(logits, dim=-1)

        for pos in target_positions:
            target_id = input_ids[pos + 1]
            doc_bits += -logprobs[pos, target_id] / log(2)

    record(doc_bits, doc_bytes)
```

Implementation detail: use KV caching and batched windows for speed. The reference implementation should be correct first, fast second.

---

## 16. Historical v0.1 implementation scope

This section records the original exact-compression implementation scope. The
current v0.3 leaderboard contract is defined in Sections 1 and 4.5.

### v0.1 must include

- CLI scoring for Hugging Face causal language models;
- tokenizer-native scoring normalized by UTF-8 bytes;
- public development suite with small text/code/multilingual samples;
- gzip/zstd/brotli/xz baselines;
- JSONL run output;
- domain-level reporting;
- bootstrap confidence intervals;
- unit tests for token shift, byte counting, and context reset;
- documentation warning that public dev scores are not contamination-safe;
- access-tier metadata in run outputs;
- documentation separating exact target-logprob scoring from generated-logprob-only APIs;
- documentation separating pure compression from reasoning-assisted / test-time-compute compression.

### v0.1 should not include

- closed API scoring unless exact target logprobs are available and verified on fixtures;
- private leaderboard;
- byte-marginalization over tokenizers;
- actual arithmetic-coded file output;
- multimodal data.

---

## 17. Milestones

### Milestone 1 — Reference scorer

Deliverables:

- Python package `cbench`;
- model adapter interface;
- Hugging Face causal LM adapter;
- dataset manifest format;
- metrics implementation;
- compressor baselines;
- tests.

Acceptance criteria:

- scoring a tiny fixture gives a known answer;
- repeated runs are stable within tolerance;
- raw byte counts match fixture manifests;
- gzip/zstd baseline results are reproducible.

### Milestone 2 — Public dev suite

Deliverables:

- `cbench-dev-small`, 5–50 MB;
- domains: prose, code, multilingual, structured;
- dataset cards with license/provenance;
- baseline leaderboard.

Acceptance criteria:

- no private or sensitive data;
- all licenses allow benchmark distribution;
- test suite validates manifest hashes.

### Milestone 3 — Conditional compression prototype

Deliverables:

- context/target manifest schema;
- label scoring mode;
- QA and translation toy tasks;
- target-boundary handling tests.

Acceptance criteria:

- only target bytes count;
- context cannot include future target content;
- delimiter and tokenizer-boundary policies are documented.

### Milestone 4 — API capability registry and exact hosted adapters

Deliverables:

- provider capability registry schema;
- fixture-based verification script for target-logprob scoring;
- optional exact hosted adapter for APIs that can score supplied targets;
- docs distinguishing exact, provider-audited, generated-logprob-only, and black-box modes.

Acceptance criteria:

- every provider that can return a valid choice can enter the API Track;
- exact diagnostics require target-scoring fixture verification;
- generated-token-only APIs are rejected from exact diagnostics;
- run metadata records provider endpoint, model fingerprint, tool/retrieval settings, and reasoning-effort setting.

### Milestone 5 — Private evaluation server

Deliverables:

- job runner;
- private data vault;
- network-isolated evaluation containers;
- aggregate score publication;
- audit logs.

Acceptance criteria:

- submitters cannot access hidden examples;
- evaluation is reproducible by benchmark administrators;
- scores include confidence intervals and domain breakdown.

### Milestone 6 — MDL / artifact track

Deliverables:

- submission packaging spec;
- artifact size accounting;
- offline decompressor/runtime policy;
- sandboxed artifact runner.

Acceptance criteria:

- model/tokenizer/dictionaries are counted;
- network is disabled;
- decompressor can reproduce data if actual coding is required, or ideal scoring mode is clearly separated.

---

## 18. Governance and release strategy

### 18.1 Public components

Public:

- scoring code;
- public dev set;
- baseline scripts;
- metric definitions;
- result schema;
- leaderboard code.

Private:

- active test examples;
- data collection details that would allow reconstruction;
- canary strings;
- evaluation random seeds where they could expose data.

### 18.2 Benchmark cycles

Recommended cycle:

- quarterly private test refresh;
- frozen scoring harness per cycle;
- public postmortem after cycle ends;
- optional delayed release of retired test shards if licensing allows.

### 18.3 Leaderboard labels

Use labels to prevent misleading comparisons:

- `open-reproducible`: open model and deterministic harness;
- `api-snapshot`: closed API with snapshot metadata;
- `approximate`: scoring limitations exist;
- `public-dev-only`: not contamination-safe;
- `retired-test`: old leaderboard no longer active.

---

## 19. Realistic failure modes

### 19.1 Model cannot score target logprobs

Mitigation: include it in the API Track; exclude it only from exact BPB
diagnostics.

### 19.2 Tokenizer boundary artifacts dominate short targets

Mitigation: use longer targets, fixed delimiters, and offset audits; report minimum target length.

### 19.3 Benchmark becomes memorized

Mitigation: rolling private sets, data provenance controls, canaries, and post-submission collection for some tracks.

### 19.4 Cost explodes for frontier models

Mitigation: use stratified sampling, report confidence intervals, and offer small/medium/full leaderboard tiers.

### 19.5 Long-context models get unfair advantage

Mitigation: separate context regimes and report context budget prominently.

### 19.6 Classical compressors beat LLMs on structured data

This is not a failure. It reveals that specialized compression remains powerful. Report domain breakdown.

### 19.7 Model size is ignored

Mitigation: maintain both Predictive and MDL tracks.

### 19.8 Reasoning settings are mixed

Mitigation: publish separate API Track entries for `low`, `medium`, `high`,
`xhigh`, or provider-specific equivalents.

### 19.9 API exposes only generated-token logprobs

Mitigation: include it in the API Track and exclude it from exact BPB
diagnostics.

---

## 20. Minimal repository structure

```text
cbench/
  README.md
  pyproject.toml
  cbench/
    __init__.py
    cli.py
    data/
      manifest.py
      loaders.py
      validation.py
    scoring/
      hf_causal.py
      api_exact.py          # optional: exact target-logprob APIs only
      windows.py
      logprob.py
      boundaries.py
    providers/
      capabilities.py       # provider access-tier registry
      verification.py       # fixture tests for target scoring support
    compressors/
      gzip_baseline.py
      zstd_baseline.py
      brotli_baseline.py
      xz_baseline.py
    metrics.py
    bootstrap.py
    report.py
  configs/
    dev_small.yaml
  datasets/
    dev_small_manifest.jsonl
  scripts/
    score_hf_model.py
    run_baselines.py
    make_report.py
  tests/
    test_byte_counts.py
    test_token_shift.py
    test_windowing.py
    test_metrics.py
    fixtures/
      tiny_utf8.txt
      tiny_code.py
      tiny_zh.txt
  docs/
    benchmark_spec.md
    contamination_policy.md
    api_model_policy.md
    reasoning_effort_policy.md
    provider_capability_registry.md
    mdl_track.md
```

---

## 21. Recommended first prototype command line

```bash
# Score a small Hugging Face model on a public dev suite.
cbench score \
  --model hf:gpt2 \
  --suite configs/dev_small.yaml \
  --context-regime small \
  --max-context-bytes 8192 \
  --target-chunk-bytes 2048 \
  --output runs/gpt2_dev_small.json

# Run classical compressor baselines.
cbench baseline \
  --suite configs/dev_small.yaml \
  --compressors gzip,zstd,brotli,xz \
  --output runs/baselines_dev_small.json

# Generate report.
cbench report \
  --inputs runs/*.json \
  --output reports/dev_small_report.md
```

---

## 22. The design choice that matters most

The core choice is whether C-Bench becomes:

1. **another public static benchmark**, which will eventually be memorized; or
2. **a living compression evaluation protocol**, with private rotating data, open scoring code, and explicit uncertainty.

The second path is much harder, but it is the version worth building.

---

## 23. One-sentence definition

**C-Bench ranks black-box language models by chance-adjusted accuracy on hidden
continuation choices, while retaining exact BPB tools as unranked compression
diagnostics.**
