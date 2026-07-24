from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import math
from typing import Any, Iterable


RAW_BPB = 8.0
SCORE_ZERO_BPB = 16.0


@dataclass(frozen=True)
class DocumentScore:
    id: str
    domain: str
    bits: float
    bytes: int
    token_count: int | None = None
    bpb: float | None = None

    def as_dict(self) -> dict[str, Any]:
        bpb = self.bpb if self.bpb is not None else bits_per_byte(self.bits, self.bytes)
        data: dict[str, Any] = {
            "id": self.id,
            "domain": self.domain,
            "bits": self.bits,
            "bytes": self.bytes,
            "bpb": bpb,
            "score_100": bpb_to_score_100(bpb),
        }
        if self.token_count is not None:
            data["token_count"] = self.token_count
        return data


def bits_per_byte(bits: float, byte_count: int) -> float:
    if not math.isfinite(bits) or bits < 0:
        raise ValueError("bits must be finite and non-negative")
    if byte_count <= 0:
        raise ValueError("byte_count must be positive")
    return bits / byte_count


def compression_ratio_raw(bpb: float) -> float:
    _validate_bpb(bpb)
    return bpb / RAW_BPB


def bpb_to_score_100(bpb: float) -> float:
    """Map BPB to a fixed 0-100 scale where higher is better.

    The anchors are 0 BPB -> 100, raw bytes (8 BPB) -> 50, and
    16 BPB -> 0. Clipping only applies outside the published scale range.
    """
    _validate_bpb(bpb)
    return max(0.0, min(100.0, 100.0 * (1.0 - bpb / SCORE_ZERO_BPB)))


def micro_bpb(documents: Iterable[DocumentScore]) -> float:
    docs = list(documents)
    total_bits = sum(doc.bits for doc in docs)
    total_bytes = sum(doc.bytes for doc in docs)
    return bits_per_byte(total_bits, total_bytes)


def domain_breakdown(documents: Iterable[DocumentScore]) -> list[dict[str, Any]]:
    grouped: dict[str, list[DocumentScore]] = defaultdict(list)
    for doc in documents:
        grouped[doc.domain].append(doc)
    rows = []
    for domain in sorted(grouped):
        docs = grouped[domain]
        rows.append(
            {
                "domain": domain,
                "bits": sum(doc.bits for doc in docs),
                "bytes": sum(doc.bytes for doc in docs),
                "documents": len(docs),
                "bpb": micro_bpb(docs),
                "score_100": bpb_to_score_100(micro_bpb(docs)),
            }
        )
    return rows


def macro_bpb(documents: Iterable[DocumentScore]) -> float:
    rows = domain_breakdown(documents)
    if not rows:
        raise ValueError("at least one document is required")
    return sum(row["bpb"] for row in rows) / len(rows)


def aggregate_scores(documents: Iterable[DocumentScore], *, bootstrap_ci: tuple[float, float] | None = None) -> dict[str, Any]:
    docs = list(documents)
    micro = micro_bpb(docs)
    macro = macro_bpb(docs)
    scores: dict[str, Any] = {
        "score_100": bpb_to_score_100(macro),
        "micro_bpb": micro,
        "micro_score_100": bpb_to_score_100(micro),
        "macro_bpb": macro,
        "compression_ratio_raw": compression_ratio_raw(micro),
        "score_scale": {
            "min": 0,
            "max": 100,
            "higher_is_better": True,
            "zero_bpb_score": 100,
            "raw_bpb": RAW_BPB,
            "raw_bpb_score": bpb_to_score_100(RAW_BPB),
            "zero_score_bpb": SCORE_ZERO_BPB,
        },
    }
    if bootstrap_ci is not None:
        scores["bootstrap_ci_95"] = [bootstrap_ci[0], bootstrap_ci[1]]
        scores["score_100_ci_95"] = [
            bpb_to_score_100(bootstrap_ci[1]),
            bpb_to_score_100(bootstrap_ci[0]),
        ]
    return scores


def relative_gain(reference_bpb: float, model_bpb: float) -> float:
    _validate_bpb(reference_bpb)
    _validate_bpb(model_bpb)
    if reference_bpb == 0:
        raise ValueError("reference_bpb must be positive")
    return (reference_bpb - model_bpb) / reference_bpb


def _validate_bpb(bpb: float) -> None:
    if not math.isfinite(bpb) or bpb < 0:
        raise ValueError("bpb must be finite and non-negative")
