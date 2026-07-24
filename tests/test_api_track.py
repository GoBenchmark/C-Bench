import pytest

from cbench.api_track import (
    ApiChoiceCase,
    ApiChoicePrediction,
    api_score_100,
    score_api_track,
)


def _case(case_id: str, domain: str, answer: int = 0) -> ApiChoiceCase:
    return ApiChoiceCase(
        id=case_id,
        domain=domain,
        candidates=("a", "b", "c", "d"),
        answer=answer,
    )


def test_api_score_is_linear_above_chance() -> None:
    assert api_score_100(0.25) == 0.0
    assert api_score_100(0.625) == 50.0
    assert api_score_100(1.0) == 100.0
    assert api_score_100(0.0) == 0.0


def test_api_track_uses_macro_domain_accuracy() -> None:
    cases = [
        _case("large-1", "large"),
        _case("large-2", "large"),
        _case("large-3", "large"),
        _case("small-1", "small"),
    ]
    predictions = [
        ApiChoicePrediction(id="large-1", choice=0),
        ApiChoicePrediction(id="large-2", choice=0),
        ApiChoicePrediction(id="large-3", choice=0),
        ApiChoicePrediction(id="small-1", choice=1),
    ]
    result = score_api_track(cases, predictions, bootstrap_samples=20)
    assert result["scores"]["micro_accuracy"] == 0.75
    assert result["scores"]["macro_accuracy"] == 0.5
    assert result["scores"]["cbench_api_score"] == pytest.approx(100.0 / 3.0)


def test_missing_predictions_count_as_incorrect() -> None:
    result = score_api_track(
        [_case("one", "domain"), _case("two", "domain")],
        [ApiChoicePrediction(id="one", choice=0)],
        bootstrap_samples=20,
    )
    assert result["scores"]["answered"] == 1
    assert result["scores"]["correct"] == 1
    assert result["scores"]["macro_accuracy"] == 0.5


def test_unknown_prediction_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown case ids"):
        score_api_track(
            [_case("known", "domain")],
            [ApiChoicePrediction(id="unknown", choice=0)],
            bootstrap_samples=20,
        )


def test_duplicate_in_memory_predictions_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate prediction ids"):
        score_api_track(
            [_case("known", "domain")],
            [
                ApiChoicePrediction(id="known", choice=0),
                ApiChoicePrediction(id="known", choice=1),
            ],
            bootstrap_samples=20,
        )


def test_duplicate_in_memory_cases_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate case ids"):
        score_api_track(
            [_case("duplicate", "a"), _case("duplicate", "b")],
            [],
            bootstrap_samples=20,
        )
