# Prompt for an AI Engineering Agent: Build C-Bench v0.2 Reference Implementation

You are an expert ML systems engineer and benchmark designer. Your task is to build the first working version of **C-Bench**, an LLM-as-compressor benchmark.

C-Bench evaluates language models by the cumulative negative log-probability they assign to held-out target text. The underlying metric is **bits per UTF-8 byte (BPB)**, where lower is better. The public headline score is a fixed 0-100 linear conversion of Macro BPB, where higher is better: 0 BPB = 100, raw bytes at 8 BPB = 50, and 16 BPB = 0. This v0.2 prompt adds explicit provider-access tiers and reasoning-effort / test-time-compute metadata. The first implementation should prioritize correctness, reproducibility, and clear interfaces over speed.

Use the design below as the build contract.

---

## Mission

Create a Python package and CLI that can:

1. Score open-weight causal language models as predictive compressors.
2. Normalize score by raw UTF-8 byte length.
3. Run classical compressor baselines.
4. Produce JSON and Markdown reports.
5. Record access-tier metadata, including whether the score came from local logits, exact target-logprob APIs, generated-logprob-only APIs, or an approximate/black-box mode.
6. Record reasoning-effort / thinking-budget metadata where applicable, but keep pure compression separate from reasoning-assisted compression.
7. Include tests that prevent common scoring errors such as target leakage, off-by-one token shifts, wrong byte counts, context-boundary mistakes, and accidental inclusion of generated-logprob-only APIs in the exact leaderboard.

Do **not** build a private leaderboard yet. Build a clean local reference implementation first. Exact API adapters may be stubbed unless a provider supports supplied-target logprobs and can pass fixture verification.

---

## Required repository structure

Create this structure:

```text
cbench/
  README.md
  pyproject.toml
  cbench/
    __init__.py
    cli.py
    data/
      __init__.py
      manifest.py
      loaders.py
      validation.py
    scoring/
      __init__.py
      hf_causal.py
      api_exact.py
      windows.py
      logprob.py
      boundaries.py
    providers/
      __init__.py
      capabilities.py
      verification.py
    compressors/
      __init__.py
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
    fixtures/
      tiny_en.txt
      tiny_code.py
      tiny_zh.txt
      tiny_json.jsonl
  scripts/
    score_hf_model.py
    run_baselines.py
    make_report.py
  tests/
    test_byte_counts.py
    test_token_shift.py
    test_windowing.py
    test_metrics.py
    test_manifest_validation.py
  docs/
    benchmark_spec.md
    contamination_policy.md
    api_model_policy.md
    reasoning_effort_policy.md
    provider_capability_registry.md
    mdl_track.md
```

---

## Core metric

Implement:

```text
bits = -sum(log2 P_model(target_token_i | context, previous_target_tokens))
BPB = bits / len(target_bytes)
compression_ratio_raw = BPB / 8
```

Use model-native tokenization, but normalize by raw UTF-8 bytes.

Do not report raw token perplexity as the primary metric.

---

## Access tiers and API eligibility

Implement access-tier metadata even if v0.2 only scores Hugging Face models locally.

Canonical exact C-Bench requires one of:

1. `open-local-logits`: evaluator computes logits/logprobs directly from local/open model weights.
2. `hosted-target-logprobs`: provider API scores a supplied `context` and exact `target` continuation.
3. `hosted-echo-prompt-logprobs`: completion-style API can echo prompt tokens and return prompt-token logprobs, verified to score `context + target` reproducibly.
4. `provider-audited-internal`: provider runs the official scorer internally and submits signed aggregate results. This is not as independently auditable.

Non-canonical / approximate tiers:

5. `generated-logprobs-only`: API returns logprobs only for generated output tokens. This is not exact C-Bench.
6. `black-box-chat-only`: no target logprobs. This is not exact C-Bench.

The implementation must prevent non-canonical tiers from being reported as exact compression scores.

Create a provider capability registry schema with fields:

```json
{
  "provider": "example",
  "endpoint_family": "openai-compatible-completions",
  "model": "example-model-snapshot",
  "access_tier": "hosted-target-logprobs",
  "supports_supplied_target_logprobs": true,
  "supports_prompt_logprobs": false,
  "supports_generated_logprobs_only": false,
  "supports_token_bytes_or_offsets": true,
  "max_context_tokens": 131072,
  "reasoning_effort_controls": ["low", "medium", "high"],
  "tools_can_be_disabled": true,
  "retrieval_can_be_disabled": true,
  "date_verified": "YYYY-MM-DD",
  "verification_fixture_sha256": "..."
}
```

For v0.2, implement the schema, validation, docs, and fixture verification hooks. A real hosted adapter is optional.

---

## Reasoning-effort / test-time-compute policy

Some reasoning models expose settings such as `reasoning_effort`, `thinking_budget`, or hidden reasoning-token budgets. These settings may change compression performance on conditional reasoning tasks and may change cost/latency.

Policy:

- Canonical pure compression must use one fixed documented setting.
- Different reasoning settings must be separate run entries, e.g. `model/medium` and `model/xhigh`.
- Reports must include `reasoning_effort`, `reasoning_tokens` if available, latency, and cost.
- Do not mix reasoning-assisted scores into the pure compression leaderboard without clear labels.
- If the model cannot return target-token logprobs under a reasoning setting, that setting is not eligible for exact C-Bench.

---

## Dataset manifest format

Use a JSONL manifest with one row per document or conditional example.

For streaming documents:

```json
{
  "id": "tiny_en_001",
  "domain": "prose",
  "path": "datasets/fixtures/tiny_en.txt",
  "mode": "streaming",
  "sha256": "...",
  "license": "fixture",
  "bytes": 1234
}
```

For future conditional examples:

```json
{
  "id": "qa_001",
  "domain": "qa",
  "mode": "conditional",
  "context_path": "...",
  "target_path": "...",
  "context_sha256": "...",
  "target_sha256": "...",
  "target_bytes": 123
}
```

For v0.1, implement streaming mode fully and create stubs/tests for conditional mode.

---

## Hugging Face scorer

Implement a Hugging Face causal LM scorer.

Requirements:

1. Accept model name or local path.
2. Load `AutoTokenizer` and `AutoModelForCausalLM`.
3. Preserve raw byte counts from the file before decoding.
4. Decode UTF-8 strictly by default. If a file is invalid UTF-8, skip it with a clear error unless `--allow-invalid-utf8` is explicitly provided.
5. Tokenize without adding special tokens unless explicitly configured.
6. Score left-to-right with correct shifted logits:
   - logits at position `i` predict token at position `i + 1`.
7. Use a rolling context window with configurable maximum context tokens or bytes.
8. Reset context at document boundaries.
9. Never score a token using future target content in the input beyond the normal teacher-forced prefix. Teacher forcing is allowed only because the logits for token `i` are computed before observing token `i`.
10. Output per-document bits, bytes, token count, BPB, and domain.

Implementation can start simple: one document at a time, no KV cache. Add batching or KV cache only after correctness tests pass.

---

## Windowing policy

Implement a function:

```python
make_windows(token_ids, max_context_tokens, target_chunk_tokens) -> list[Window]
```

Each `Window` should contain:

```python
@dataclass
class Window:
    context_ids: list[int]
    target_ids: list[int]
    target_start_absolute_token: int
    target_end_absolute_token: int
```

Policy:

- First target chunk begins at token 0 or token 1 depending on BOS policy. Document this explicitly.
- For a simple v0.1 implementation, score token `j` with all previous tokens up to the context cap.
- No document may use context from another document.
- Every target token should be scored exactly once, except any unavoidable first-token/BOS policy must be documented and tested.

Preferred v0.1 policy:

- If the tokenizer/model has a BOS token and `--use-bos` is enabled, prepend BOS and score the first real token from BOS.
- Otherwise, skip the first token of each document because no previous context exists. Report `unscored_initial_tokens`.

---

## Compressor baselines

Implement baselines over raw bytes:

- gzip using Python stdlib;
- zstd if `zstandard` is installed, otherwise warn and skip;
- brotli if `brotli` is installed, otherwise warn and skip;
- xz/lzma using Python stdlib.

For each document and compressor, report:

```json
{
  "compressor": "gzip",
  "id": "tiny_en_001",
  "domain": "prose",
  "raw_bytes": 1234,
  "compressed_bytes": 456,
  "bpb": 2.955
}
```

Use the same manifest and domain structure as model scoring.

---

## Metrics and reports

Implement:

- per-document BPB;
- micro BPB;
- macro BPB over domains;
- domain breakdown;
- compression ratio against raw bytes;
- relative gain/loss versus gzip and zstd when baselines are available;
- bootstrap confidence intervals over documents.

Output JSON with this shape:

```json
{
  "benchmark_version": "cbench-0.1",
  "run_type": "hf_model",
  "suite": "dev_small",
  "model": {
    "name": "...",
    "access_tier": "open-local-logits",
    "provider": null,
    "endpoint_family": null,
    "model_fingerprint": null,
    "reasoning_effort": null,
    "tools": "disabled",
    "retrieval": "disabled"
  },
  "scores": {
    "micro_bpb": 1.23,
    "macro_bpb": 1.25,
    "compression_ratio_raw": 0.15375,
    "bootstrap_ci_95": [1.20, 1.30]
  },
  "domain_breakdown": [...],
  "documents": [...],
  "resources": {
    "wall_time_seconds": null,
    "peak_vram_gb": null,
    "peak_ram_gb": null,
    "tokens_per_second": null,
    "estimated_cost_usd": null,
    "api_calls": null,
    "reasoning_tokens": null
  }
}
```

Also generate a Markdown report summarizing the run.

---

## CLI commands

Implement these commands:

```bash
cbench validate --suite configs/dev_small.yaml

cbench score \
  --model hf:gpt2 \
  --suite configs/dev_small.yaml \
  --max-context-tokens 1024 \
  --target-chunk-tokens 256 \
  --output runs/gpt2_dev_small.json

cbench baseline \
  --suite configs/dev_small.yaml \
  --compressors gzip,zstd,brotli,xz \
  --output runs/baselines_dev_small.json

cbench report \
  --inputs runs/*.json \
  --output reports/dev_small_report.md
```

Use `argparse`, `typer`, or `click`. Prefer simple and stable.

---

## Tests that must pass

Create unit tests for:

1. **Byte counts**: UTF-8 byte length differs from Python string length for Chinese; verify BPB denominator uses bytes, not characters.
2. **Token shift**: verify logits at position `i` score token `i+1`, not token `i`.
3. **Window coverage**: every target token is scored exactly once according to the BOS policy.
4. **Document reset**: context from document A must not leak into document B.
5. **Manifest hash validation**: SHA-256 mismatch should fail.
6. **Metric aggregation**: micro and macro BPB differ correctly on imbalanced domains.
7. **Compressor baseline sanity**: repeated text compresses to lower BPB than random-looking text.
8. **No target leakage in conditional stubs**: context and target are stored separately and target bytes are counted separately.
9. **Access-tier validation**: generated-logprobs-only and black-box-chat-only entries cannot be marked as exact C-Bench.
10. **Reasoning metadata separation**: runs with different reasoning_effort values are separate entries and cannot overwrite each other.

---

## Development dataset

Create a tiny public fixture suite:

- `tiny_en.txt`: repeated English prose and a short non-repeated paragraph;
- `tiny_code.py`: a short Python file with repeated identifiers and structure;
- `tiny_zh.txt`: Simplified Chinese text to test UTF-8 byte counting;
- `tiny_json.jsonl`: structured repeated records.

These fixtures are for correctness only. State clearly that they are not meaningful leaderboard data.

---

## Engineering standards

- Use type hints.
- Keep code readable.
- Make all scoring assumptions explicit in docs.
- Avoid hidden global state.
- Do not silently normalize Unicode.
- Do not strip whitespace.
- Do not change line endings.
- Hash raw bytes, not decoded text.
- Prefer correctness over speed.
- Include clear error messages.

---

## Documentation to write

Write these docs:

1. `docs/benchmark_spec.md` — metric, tracks, scoring assumptions.
2. `docs/contamination_policy.md` — why public dev data is not enough, how private test data should be handled later.
3. `docs/api_model_policy.md` — exact target logprob requirement; approximate API models must be separated.
4. `docs/reasoning_effort_policy.md` — why reasoning effort / test-time compute must be fixed or reported as a separate track.
5. `docs/provider_capability_registry.md` — provider access tiers, verification fixture, and fields required for exact eligibility.
6. `docs/mdl_track.md` — future artifact-size-inclusive track inspired by classical compression benchmarks.

---

## Acceptance criteria for v0.1

The build is acceptable when:

1. `pip install -e .` works.
2. `pytest` passes.
3. `cbench validate --suite configs/dev_small.yaml` passes.
4. `cbench baseline --suite configs/dev_small.yaml --compressors gzip,xz --output runs/baselines.json` works.
5. `cbench score --model hf:gpt2 --suite configs/dev_small.yaml --output runs/gpt2.json` works on a machine with the required model dependencies.
6. The JSON output includes per-document and aggregate BPB.
7. The Markdown report is generated from run JSON files.
8. README includes installation, scoring, baseline, and report examples.
9. The docs explicitly warn that the public fixture suite is not contamination-safe and not a real leaderboard.
10. Run outputs include access_tier and reasoning_effort fields.
11. Provider capability validation rejects non-exact API modes from the canonical leaderboard.
12. Reasoning-effort docs explain that `medium`, `high`, and `xhigh`-style settings must be separate entries if benchmarked.

---

## Important conceptual guardrails

- C-Bench is not asking the model to generate compressed files.
- C-Bench uses negative log-probability as the ideal code length.
- Bits per byte is the primary metric because token perplexity is not comparable across tokenizers.
- Public datasets are for development only; a real leaderboard requires hidden, rotating, contamination-resistant data.
- Closed APIs without exact target-token logprobs cannot receive canonical scores.
- APIs that expose only generated-token logprobs are not exact model-as-compressor interfaces.
- Reasoning-effort / test-time-compute settings must be fixed for canonical pure compression or reported as separate reasoning-assisted entries.
- Do not count context bytes in conditional tasks unless the track explicitly says to.
- Do not mix model-as-compressor evaluation with model-weight compression or quantization benchmarks; those are different concepts.

---

## First implementation plan

Work in this order:

1. Create package skeleton and fixture files.
2. Implement manifest validation and SHA-256 hashing.
3. Implement compressor baselines.
4. Implement metrics and bootstrap.
5. Implement provider capability registry schema and validation.
6. Implement simple Hugging Face scorer without KV cache.
7. Add tests for byte counts, token shift, windowing, access-tier validation, and reasoning metadata separation.
8. Add CLI commands.
9. Add Markdown reporting.
10. Write docs, including API and reasoning-effort policies.
11. Run end-to-end examples and fix edge cases.

At every step, prefer a small correct implementation over a fast but ambiguous one.
