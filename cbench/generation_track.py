from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
import json
import math
from pathlib import Path
import random
from typing import Any, Iterable


SCORE_NINES = 3.0


@dataclass(frozen=True)
class GenerationCase:
    id: str
    domain: str
    target: str


@dataclass(frozen=True)
class GenerationPrediction:
    id: str
    continuation: str


def similarity_to_score(similarity: float, *, score_nines: float = SCORE_NINES) -> float:
    """Map similarity to 0-100; each 10x mismatch reduction adds equal points."""
    if not 0.0 <= similarity <= 1.0:
        raise ValueError("similarity must be between 0 and 1")
    if score_nines <= 0:
        raise ValueError("score_nines must be positive")
    if similarity == 1.0:
        return 100.0
    nines = math.log10(1.0 / (1.0 - similarity))
    return 100.0 * min(1.0, max(0.0, nines / score_nines))


def byte_similarity(target: str, continuation: str) -> float:
    return SequenceMatcher(None, target.encode(), continuation.encode()).ratio()


def load_generation_cases(path: str | Path) -> list[GenerationCase]:
    rows = _load_jsonl(path)
    cases: list[GenerationCase] = []
    seen: set[str] = set()
    for row in rows:
        case_id = _required_string(row, "id")
        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        cases.append(
            GenerationCase(
                id=case_id,
                domain=_required_string(row, "domain"),
                target=_required_string(row, "target"),
            )
        )
    if not cases:
        raise ValueError("at least one generation case is required")
    return cases


def load_generation_predictions(path: str | Path) -> list[GenerationPrediction]:
    rows = _load_jsonl(path)
    predictions: list[GenerationPrediction] = []
    seen: set[str] = set()
    for row in rows:
        case_id = _required_string(row, "id")
        if case_id in seen:
            raise ValueError(f"duplicate prediction id: {case_id}")
        seen.add(case_id)
        continuation = row.get("continuation")
        if not isinstance(continuation, str):
            raise ValueError(f"{case_id}: continuation must be a string")
        predictions.append(
            GenerationPrediction(id=case_id, continuation=continuation)
        )
    return predictions


def score_generation_track(
    cases: Iterable[GenerationCase],
    predictions: Iterable[GenerationPrediction],
    *,
    bootstrap_samples: int = 2000,
    bootstrap_seed: int = 0,
) -> dict[str, Any]:
    case_rows = list(cases)
    prediction_rows = list(predictions)
    if not case_rows:
        raise ValueError("at least one generation case is required")

    for case in case_rows:
        if not isinstance(case.id, str) or not case.id.strip():
            raise ValueError("generation case id must be a non-empty string")
        if not isinstance(case.domain, str) or not case.domain.strip():
            raise ValueError(f"{case.id}: domain must be a non-empty string")
        if not isinstance(case.target, str) or not case.target:
            raise ValueError(f"{case.id}: target must be a non-empty string")
    case_ids = [case.id for case in case_rows]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("generation cases contain duplicate case ids")

    for prediction in prediction_rows:
        if not isinstance(prediction.id, str) or not prediction.id.strip():
            raise ValueError("prediction id must be a non-empty string")
        if not isinstance(prediction.continuation, str):
            raise ValueError(f"{prediction.id}: continuation must be a string")
    prediction_ids = [prediction.id for prediction in prediction_rows]
    if len(prediction_ids) != len(set(prediction_ids)):
        raise ValueError("generation predictions contain duplicate prediction ids")

    case_id_set = set(case_ids)
    prediction_by_id = {prediction.id: prediction for prediction in prediction_rows}
    unknown = sorted(set(prediction_by_id) - case_id_set)
    if unknown:
        raise ValueError(f"predictions contain unknown case ids: {', '.join(unknown)}")

    results = []
    for case in case_rows:
        prediction = prediction_by_id.get(case.id)
        continuation = prediction.continuation if prediction is not None else ""
        target_bytes = case.target.encode()
        continuation_bytes = continuation.encode()
        prefix_bytes = 0
        for target_byte, predicted_byte in zip(target_bytes, continuation_bytes):
            if target_byte != predicted_byte:
                break
            prefix_bytes += 1
        results.append(
            {
                "id": case.id,
                "domain": case.domain,
                "answered": prediction is not None,
                "similarity": byte_similarity(case.target, continuation),
                "prefix": prefix_bytes / len(target_bytes),
                "exact": continuation_bytes == target_bytes,
            }
        )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[str(result["domain"])].append(result)

    domain_breakdown = []
    for domain in sorted(grouped):
        rows = grouped[domain]
        mean_similarity = _mean(rows, "similarity")
        domain_breakdown.append(
            {
                "domain": domain,
                "cases": len(rows),
                "answered": sum(bool(row["answered"]) for row in rows),
                "similarity": mean_similarity,
                "cbench_score": similarity_to_score(mean_similarity),
                "prefix": _mean(rows, "prefix"),
                "exact": sum(bool(row["exact"]) for row in rows),
            }
        )

    macro_similarity = sum(
        row["similarity"] for row in domain_breakdown
    ) / len(domain_breakdown)
    score_ci = _bootstrap_score_ci(
        grouped,
        samples=bootstrap_samples,
        seed=bootstrap_seed,
    )
    return {
        "scores": {
            "cbench_score": similarity_to_score(macro_similarity),
            "score_100_ci_95": list(score_ci),
            "macro_similarity": macro_similarity,
            "micro_similarity": _mean(results, "similarity"),
            "macro_prefix": sum(row["prefix"] for row in domain_breakdown)
            / len(domain_breakdown),
            "exact_rate": sum(bool(row["exact"]) for row in results) / len(results),
            "exact": sum(bool(row["exact"]) for row in results),
            "cases": len(results),
            "answered": sum(bool(row["answered"]) for row in results),
            "score_nines": SCORE_NINES,
            "higher_is_better": True,
        },
        "domain_breakdown": domain_breakdown,
        "results": results,
    }


def _bootstrap_score_ci(
    grouped: dict[str, list[dict[str, Any]]],
    *,
    samples: int,
    seed: int,
) -> tuple[float, float]:
    if samples <= 0:
        raise ValueError("bootstrap_samples must be positive")
    rng = random.Random(seed)
    values = []
    for _ in range(samples):
        domain_similarities = []
        for domain in sorted(grouped):
            rows = grouped[domain]
            sampled = [rows[rng.randrange(len(rows))] for _ in rows]
            domain_similarities.append(_mean(sampled, "similarity"))
        values.append(
            similarity_to_score(
                sum(domain_similarities) / len(domain_similarities)
            )
        )
    values.sort()
    return (
        values[int(0.025 * (len(values) - 1))],
        values[int(0.975 * (len(values) - 1))],
    )


def _mean(rows: list[dict[str, Any]], key: str) -> float:
    return sum(float(row[key]) for row in rows) / len(rows)


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows = []
    for line_number, line in enumerate(
        Path(path).read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: expected a JSON object")
        rows.append(value)
    return rows


def _required_string(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value
