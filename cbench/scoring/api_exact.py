from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExactApiScore:
    target_token_logprobs: list[float]
    total_logprob_target: float
    token_count: int
    byte_count: int
    model_fingerprint: str | None = None


class ExactApiScorer:
    def score(self, context: str, target: str) -> ExactApiScore:
        raise NotImplementedError("Exact hosted target-logprob adapters are not implemented")
