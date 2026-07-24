from __future__ import annotations

import math
from typing import Sequence


def negative_logprob_bits(logprob_natural: float) -> float:
    return -logprob_natural / math.log(2.0)


def sum_negative_logprob_bits(logprobs_natural: Sequence[float]) -> float:
    return sum(negative_logprob_bits(value) for value in logprobs_natural)


def target_prediction_positions(context_len: int, target_count: int) -> list[tuple[int, int]]:
    """Return (prediction_position, target_input_position) pairs for teacher forcing."""
    if context_len < 0 or target_count < 0:
        raise ValueError("context_len and target_count must be non-negative")
    pairs: list[tuple[int, int]] = []
    for offset in range(target_count):
        target_input_position = context_len + offset
        prediction_position = target_input_position - 1
        if prediction_position >= 0:
            pairs.append((prediction_position, target_input_position))
    return pairs
