# Provider Capability Registry

Provider entries record whether a model endpoint can participate in exact
C-Bench scoring.

Required fields:

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

Exact hosted scoring requires target or prompt logprobs, token byte/offset
information, fixed model identity, and controls to disable tools and retrieval.
