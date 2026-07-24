# Contamination Policy

Public C-Bench fixtures are for development only. A real leaderboard requires
hidden, rotating, contamination-resistant test data.

Threats include training-set overlap, benchmark leakage through submissions,
closed-model logging, silent API model updates, and memorized canaries.

Operational policy for future private evaluations:

- Keep active test examples private.
- Refresh test shards periodically.
- Prefer licensed, newly written, or commissioned material.
- Record model snapshot IDs, submission dates, tool settings, and reasoning settings.
- Disable tools, retrieval, browsing, and memory for canonical runs.
- Do not send private test data to providers without suitable audit and no-training terms.
- Use canaries and near-duplicate checks, but do not treat canaries as proof that no contamination exists.
