# OpenRouter Public Results

These are recovered results from a maintainer-run OpenRouter evaluation on
July 24, 2026. No new model requests were made for this submission.

## Protocol

- Suite: released `public_dev` generation cases, one case per domain
- Context: 600 characters
- Target: the immediately following 80 characters, hidden from the model
- Endpoint: OpenRouter `chat/completions`
- Temperature: 0
- Maximum output: 128 tokens
- Reasoning budget: 16 tokens, excluded from returned text
- Tools, retrieval, browsing, and memory: not provided to the models
- Scorer: C-Bench 0.3.0

The raw continuations were recovered from the original local task log. Rescoring
them against the released cases reproduced every original domain similarity
exactly, with zero numerical drift.

| Model | Complete cases | C-Bench Score | Macro similarity | Macro prefix | Exact |
|---|---:|---:|---:|---:|---:|
| nvidia/nemotron-3-ultra-550b-a55b:free | 4/4 | 4.47 | 26.58% | 26.90% | 0/4 |
| openai/gpt-oss-20b:free | 4/4 | 2.23 | 14.27% | 0.00% | 0/4 |

`google/gemma-4-31b-it:free` is not listed because all four original requests
returned HTTP 429 and produced no scorable continuations.

See [report.md](report.md) for the generated C-Bench report. Each model also has
a raw prediction JSONL file and a full score JSON file in this directory.
