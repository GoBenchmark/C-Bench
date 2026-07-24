from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


EXACT_ACCESS_TIERS = {
    "open-local-logits",
    "hosted-target-logprobs",
    "hosted-echo-prompt-logprobs",
    "provider-audited-internal",
}

NON_CANONICAL_ACCESS_TIERS = {
    "generated-logprobs-only",
    "black-box-chat-only",
}

ALL_ACCESS_TIERS = EXACT_ACCESS_TIERS | NON_CANONICAL_ACCESS_TIERS


@dataclass(frozen=True)
class ProviderCapability:
    provider: str
    endpoint_family: str
    model: str
    access_tier: str
    supports_supplied_target_logprobs: bool
    supports_prompt_logprobs: bool
    supports_generated_logprobs_only: bool
    supports_token_bytes_or_offsets: bool
    max_context_tokens: int | None
    reasoning_effort_controls: list[str] = field(default_factory=list)
    tools_can_be_disabled: bool = True
    retrieval_can_be_disabled: bool = True
    date_verified: str | None = None
    verification_fixture_sha256: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProviderCapability":
        return cls(
            provider=str(data["provider"]),
            endpoint_family=str(data["endpoint_family"]),
            model=str(data["model"]),
            access_tier=str(data["access_tier"]),
            supports_supplied_target_logprobs=bool(data.get("supports_supplied_target_logprobs", False)),
            supports_prompt_logprobs=bool(data.get("supports_prompt_logprobs", False)),
            supports_generated_logprobs_only=bool(data.get("supports_generated_logprobs_only", False)),
            supports_token_bytes_or_offsets=bool(data.get("supports_token_bytes_or_offsets", False)),
            max_context_tokens=data.get("max_context_tokens"),
            reasoning_effort_controls=list(data.get("reasoning_effort_controls", [])),
            tools_can_be_disabled=bool(data.get("tools_can_be_disabled", False)),
            retrieval_can_be_disabled=bool(data.get("retrieval_can_be_disabled", False)),
            date_verified=data.get("date_verified"),
            verification_fixture_sha256=data.get("verification_fixture_sha256"),
        )


def is_exact_access_tier(access_tier: str) -> bool:
    return access_tier in EXACT_ACCESS_TIERS


def validate_capability(capability: ProviderCapability, *, require_exact: bool = False) -> None:
    if capability.access_tier not in ALL_ACCESS_TIERS:
        raise ValueError(f"Unknown access_tier: {capability.access_tier}")
    if require_exact and capability.access_tier in NON_CANONICAL_ACCESS_TIERS:
        raise ValueError(f"{capability.access_tier} is not eligible for exact C-Bench")
    if capability.access_tier == "hosted-target-logprobs" and not capability.supports_supplied_target_logprobs:
        raise ValueError("hosted-target-logprobs requires supports_supplied_target_logprobs=true")
    if capability.access_tier == "hosted-echo-prompt-logprobs" and not capability.supports_prompt_logprobs:
        raise ValueError("hosted-echo-prompt-logprobs requires supports_prompt_logprobs=true")
    if capability.access_tier in {"hosted-target-logprobs", "hosted-echo-prompt-logprobs"}:
        if not capability.supports_token_bytes_or_offsets:
            raise ValueError("exact hosted scoring requires token bytes or offsets")
        if not capability.tools_can_be_disabled or not capability.retrieval_can_be_disabled:
            raise ValueError("exact hosted scoring requires tools and retrieval to be disableable")


def canonical_model_metadata(
    *,
    name: str,
    access_tier: str = "open-local-logits",
    provider: str | None = None,
    endpoint_family: str | None = None,
    model_fingerprint: str | None = None,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    if not is_exact_access_tier(access_tier):
        raise ValueError(f"{access_tier} is not eligible for exact C-Bench")
    return {
        "name": name,
        "access_tier": access_tier,
        "provider": provider,
        "endpoint_family": endpoint_family,
        "model_fingerprint": model_fingerprint,
        "reasoning_effort": reasoning_effort,
        "tools": "disabled",
        "retrieval": "disabled",
    }
