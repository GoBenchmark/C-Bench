from __future__ import annotations

import random
from typing import Sequence

from cbench.metrics import DocumentScore, macro_bpb


def bootstrap_macro_bpb_ci(
    documents: Sequence[DocumentScore],
    *,
    samples: int = 1000,
    confidence: float = 0.95,
    seed: int = 13,
) -> tuple[float, float]:
    if not documents:
        raise ValueError("at least one document is required")
    if samples <= 0:
        raise ValueError("samples must be positive")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    rng = random.Random(seed)
    values: list[float] = []
    n = len(documents)
    for _ in range(samples):
        draw = [documents[rng.randrange(n)] for _ in range(n)]
        values.append(macro_bpb(draw))
    values.sort()
    alpha = 1.0 - confidence
    low_index = max(0, int((alpha / 2.0) * samples))
    high_index = min(samples - 1, int((1.0 - alpha / 2.0) * samples) - 1)
    return values[low_index], values[high_index]
