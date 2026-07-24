import pytest

from cbench.providers.capabilities import ProviderCapability, canonical_model_metadata, validate_capability


def test_generated_logprobs_only_cannot_be_exact() -> None:
    capability = ProviderCapability(
        provider="example",
        endpoint_family="chat",
        model="example-model",
        access_tier="generated-logprobs-only",
        supports_supplied_target_logprobs=False,
        supports_prompt_logprobs=False,
        supports_generated_logprobs_only=True,
        supports_token_bytes_or_offsets=False,
        max_context_tokens=8192,
    )
    with pytest.raises(ValueError, match="not eligible"):
        validate_capability(capability, require_exact=True)


def test_black_box_chat_only_metadata_rejected_for_exact_run() -> None:
    with pytest.raises(ValueError, match="not eligible"):
        canonical_model_metadata(name="chat-only", access_tier="black-box-chat-only")


def test_reasoning_effort_metadata_keeps_entries_separate() -> None:
    low = canonical_model_metadata(name="model", reasoning_effort="low")
    high = canonical_model_metadata(name="model", reasoning_effort="high")
    assert low != high
    assert low["reasoning_effort"] == "low"
    assert high["reasoning_effort"] == "high"
