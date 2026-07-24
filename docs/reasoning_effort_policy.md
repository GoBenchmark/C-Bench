# Reasoning-Effort Policy

Reasoning models may expose settings such as `reasoning_effort`,
`thinking_budget`, or hidden reasoning-token budgets. These settings can change
quality, latency, cost, and reproducibility.

Policy:

- Different reasoning settings are separate run entries, such as `model/medium`
  and `model/xhigh`.
- Reports include `reasoning_effort`, reasoning tokens if available, latency,
  and estimated cost.
- API Track leaderboard entries must use a fixed documented setting and disable
  tools, retrieval, browsing, and memory.
- Reasoning effort may improve predictive-choice accuracy, but its cost and
  latency remain separate reported quantities.
- Exact compression diagnostics may use reasoning settings only when the model
  returns target-token logprobs; those diagnostics are not leaderboard entries.
