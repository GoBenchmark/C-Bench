# Provider Capability Registry

Provider entries record how a model participates in the Generation Track and
whether it also supports optional API-choice and exact compression diagnostics.

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

All black-box text APIs can participate in the Generation Track if they can
return continuation text with tools and retrieval disabled. Exact diagnostic
scoring additionally requires target or prompt logprobs, token byte/offset
information, and fixed model identity.
