from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
import random
from pathlib import Path
from typing import Any, Iterable


API_CANDIDATE_COUNT = 4


@dataclass(frozen=True)
class ApiChoiceCase:
    id: str
    domain: str
    candidates: tuple[str, ...]
    answer: int


@dataclass(frozen=True)
class ApiChoicePrediction:
    id: str
    choice: int


def api_score_100(accuracy: float, *, candidate_count: int = API_CANDIDATE_COUNT) -> float:
    """Convert choice accuracy to a chance-adjusted 0-100 score."""
    if not 0.0 <= accuracy <= 1.0:
        raise ValueError("accuracy must be between 0 and 1")
    if candidate_count < 2:
        raise ValueError("candidate_count must be at least 2")
    chance = 1.0 / candidate_count
    adjusted = (accuracy - chance) / (1.0 - chance)
    return max(0.0, min(100.0, 100.0 * adjusted))


def load_api_cases(path: str | Path) -> list[ApiChoiceCase]:
    rows = _load_jsonl(path)
    cases: list[ApiChoiceCase] = []
    seen: set[str] = set()
    for row in rows:
        case_id = _required_string(row, "id")
        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        seen.add(case_id)
        domain = _required_string(row, "domain")
        candidates = row.get("candidates")
        if not isinstance(candidates, list) or not all(
            isinstance(candidate, str) and candidate for candidate in candidates
        ):
            raise ValueError(f"{case_id}: candidates must be non-empty strings")
        if len(candidates) != API_CANDIDATE_COUNT:
            raise ValueError(
                f"{case_id}: expected {API_CANDIDATE_COUNT} candidates, got {len(candidates)}"
            )
        if len(set(candidates)) != API_CANDIDATE_COUNT:
            raise ValueError(f"{case_id}: candidates must be unique")
        answer = row.get("answer")
        if not isinstance(answer, int) or isinstance(answer, bool):
            raise ValueError(f"{case_id}: answer must be an integer")
        if not 0 <= answer < len(candidates):
            raise ValueError(f"{case_id}: answer is outside the candidate range")
        cases.append(
            ApiChoiceCase(
                id=case_id,
                domain=domain,
                candidates=tuple(candidates),
                answer=answer,
            )
        )
    if not cases:
        raise ValueError("at least one API Track case is required")
    return cases


def load_api_predictions(path: str | Path) -> list[ApiChoicePrediction]:
    rows = _load_jsonl(path)
    predictions: list[ApiChoicePrediction] = []
    seen: set[str] = set()
    for row in rows:
        case_id = _required_string(row, "id")
        if case_id in seen:
            raise ValueError(f"duplicate prediction id: {case_id}")
        seen.add(case_id)
        choice = row.get("choice")
        if not isinstance(choice, int) or isinstance(choice, bool):
            raise ValueError(f"{case_id}: choice must be an integer")
        if not 0 <= choice < API_CANDIDATE_COUNT:
            raise ValueError(f"{case_id}: choice is outside the candidate range")
        predictions.append(ApiChoicePrediction(id=case_id, choice=choice))
    return predictions


def score_api_track(
    cases: Iterable[ApiChoiceCase],
    predictions: Iterable[ApiChoicePrediction],
    *,
    bootstrap_samples: int = 2000,
    bootstrap_seed: int = 0,
) -> dict[str, Any]:
    case_rows = list(cases)
    prediction_rows = list(predictions)
    if not case_rows:
        raise ValueError("at least one API Track case is required")

    for case in case_rows:
        if not isinstance(case.id, str) or not case.id.strip():
            raise ValueError("API Track case id must be a non-empty string")
        if not isinstance(case.domain, str) or not case.domain.strip():
            raise ValueError(f"{case.id}: domain must be a non-empty string")
        valid_candidates = isinstance(case.candidates, (list, tuple)) and len(
            case.candidates
        ) == API_CANDIDATE_COUNT
        if valid_candidates:
            valid_candidates = all(
                isinstance(candidate, str) and candidate for candidate in case.candidates
            )
        if not valid_candidates:
            raise ValueError(
                f"{case.id}: expected {API_CANDIDATE_COUNT} non-empty candidates"
            )
        if len(set(case.candidates)) != API_CANDIDATE_COUNT:
            raise ValueError(f"{case.id}: candidates must be unique")
        if (
            not isinstance(case.answer, int)
            or isinstance(case.answer, bool)
            or not 0 <= case.answer < API_CANDIDATE_COUNT
        ):
            raise ValueError(f"{case.id}: answer is outside the candidate range")
    case_ids = [case.id for case in case_rows]
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("API Track cases contain duplicate case ids")

    for prediction in prediction_rows:
        if not isinstance(prediction.id, str) or not prediction.id.strip():
            raise ValueError("prediction id must be a non-empty string")
        if (
            not isinstance(prediction.choice, int)
            or isinstance(prediction.choice, bool)
            or not 0 <= prediction.choice < API_CANDIDATE_COUNT
        ):
            raise ValueError(f"{prediction.id}: choice is outside the candidate range")
    prediction_ids = [prediction.id for prediction in prediction_rows]
    if len(prediction_ids) != len(set(prediction_ids)):
        raise ValueError("API Track predictions contain duplicate prediction ids")

    case_id_set = set(case_ids)
    prediction_by_id = {prediction.id: prediction for prediction in prediction_rows}
    unknown = sorted(set(prediction_by_id) - case_id_set)
    if unknown:
        raise ValueError(f"predictions contain unknown case ids: {', '.join(unknown)}")

    results = []
    for case in case_rows:
        prediction = prediction_by_id.get(case.id)
        results.append(
            {
                "id": case.id,
                "domain": case.domain,
                "answered": prediction is not None,
                "correct": prediction is not None and prediction.choice == case.answer,
            }
        )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        grouped[str(result["domain"])].append(result)

    domain_breakdown = []
    for domain in sorted(grouped):
        rows = grouped[domain]
        correct = sum(bool(row["correct"]) for row in rows)
        accuracy = correct / len(rows)
        domain_breakdown.append(
            {
                "domain": domain,
                "cases": len(rows),
                "answered": sum(bool(row["answered"]) for row in rows),
                "correct": correct,
                "accuracy": accuracy,
                "api_score_100": api_score_100(accuracy),
            }
        )

    macro_accuracy = sum(row["accuracy"] for row in domain_breakdown) / len(
        domain_breakdown
    )
    micro_accuracy = sum(bool(row["correct"]) for row in results) / len(results)
    score = api_score_100(macro_accuracy)
    score_ci = _bootstrap_score_ci(
        grouped,
        samples=bootstrap_samples,
        seed=bootstrap_seed,
    )
    return {
        "scores": {
            "cbench_api_score": score,
            "score_100_ci_95": list(score_ci),
            "macro_accuracy": macro_accuracy,
            "micro_accuracy": micro_accuracy,
            "chance_accuracy": 1.0 / API_CANDIDATE_COUNT,
            "candidate_count": API_CANDIDATE_COUNT,
            "cases": len(results),
            "answered": sum(bool(row["answered"]) for row in results),
            "correct": sum(bool(row["correct"]) for row in results),
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
    domains = sorted(grouped)
    for _ in range(samples):
        domain_accuracies = []
        for domain in domains:
            rows = grouped[domain]
            sampled = [rows[rng.randrange(len(rows))] for _ in rows]
            domain_accuracies.append(
                sum(bool(row["correct"]) for row in sampled) / len(sampled)
            )
        values.append(api_score_100(sum(domain_accuracies) / len(domain_accuracies)))
    values.sort()
    low_index = int(0.025 * (len(values) - 1))
    high_index = int(0.975 * (len(values) - 1))
    return values[low_index], values[high_index]


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
