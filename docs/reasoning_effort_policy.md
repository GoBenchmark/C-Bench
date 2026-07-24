# Reasoning-Effort Policy

Reasoning models may expose settings such as `reasoning_effort`,
`thinking_budget`, or hidden reasoning-token budgets. These settings can change
quality, latency, cost, and reproducibility.

Policy:

- Canonical pure compression uses one fixed documented setting.
- Different reasoning settings are separate run entries, such as `model/medium`
  and `model/xhigh`.
- Reports include `reasoning_effort`, reasoning tokens if available, latency,
  and estimated cost.
- Reasoning-assisted results must not be mixed into the pure compression
  leaderboard without clear labeling.
- If a model cannot return target-token logprobs under a reasoning setting, that
  setting is not eligible for exact C-Bench.
