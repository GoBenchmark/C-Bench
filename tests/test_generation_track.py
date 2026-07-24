import pytest

from cbench.generation_track import (
    GenerationCase,
    GenerationPrediction,
    byte_similarity,
    score_generation_track,
    similarity_to_score,
)


def _case(case_id: str, domain: str, target: str = "abcd") -> GenerationCase:
    return GenerationCase(id=case_id, domain=domain, target=target)


def test_log_score_anchors() -> None:
    assert similarity_to_score(0.0) == 0.0
    assert similarity_to_score(0.9) == pytest.approx(100.0 / 3.0)
    assert similarity_to_score(0.99) == pytest.approx(200.0 / 3.0)
    assert similarity_to_score(0.999) == pytest.approx(100.0)
    assert similarity_to_score(1.0) == 100.0


def test_byte_similarity_is_exact_at_one() -> None:
    assert byte_similarity("hello", "hello") == 1.0
    assert byte_similarity("hello", "") == 0.0


def test_generation_score_uses_macro_domain_similarity() -> None:
    cases = [
        _case("large-1", "large"),
        _case("large-2", "large"),
        _case("large-3", "large"),
        _case("small-1", "small"),
    ]
    predictions = [
        GenerationPrediction(id="large-1", continuation="abcd"),
        GenerationPrediction(id="large-2", continuation="abcd"),
        GenerationPrediction(id="large-3", continuation="abcd"),
        GenerationPrediction(id="small-1", continuation=""),
    ]
    result = score_generation_track(cases, predictions, bootstrap_samples=20)
    assert result["scores"]["micro_similarity"] == 0.75
    assert result["scores"]["macro_similarity"] == 0.5
    assert result["scores"]["cbench_score"] == pytest.approx(
        similarity_to_score(0.5)
    )


def test_missing_predictions_score_zero() -> None:
    result = score_generation_track(
        [_case("one", "domain"), _case("two", "domain")],
        [GenerationPrediction(id="one", continuation="abcd")],
        bootstrap_samples=20,
    )
    assert result["scores"]["answered"] == 1
    assert result["scores"]["macro_similarity"] == 0.5
    assert result["scores"]["exact"] == 1


def test_unknown_prediction_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown case ids"):
        score_generation_track(
            [_case("known", "domain")],
            [GenerationPrediction(id="unknown", continuation="abcd")],
            bootstrap_samples=20,
        )


def test_duplicate_in_memory_predictions_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate prediction ids"):
        score_generation_track(
            [_case("known", "domain")],
            [
                GenerationPrediction(id="known", continuation="abcd"),
                GenerationPrediction(id="known", continuation="wrong"),
            ],
            bootstrap_samples=20,
        )


def test_duplicate_in_memory_cases_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate case ids"):
        score_generation_track(
            [_case("duplicate", "a"), _case("duplicate", "b")],
            [],
            bootstrap_samples=20,
        )


def test_empty_in_memory_target_is_rejected_cleanly() -> None:
    with pytest.raises(ValueError, match="target must be a non-empty string"):
        score_generation_track(
            [_case("empty", "domain", target="")],
            [],
            bootstrap_samples=20,
        )
