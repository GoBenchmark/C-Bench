import pytest

from cbench.metrics import (
    DocumentScore,
    bpb_to_score_100,
    domain_breakdown,
    macro_bpb,
    micro_bpb,
    relative_gain,
)


def test_micro_and_macro_differ_on_imbalanced_domains() -> None:
    docs = [
        DocumentScore(id="a", domain="large", bits=100.0, bytes=100),
        DocumentScore(id="b", domain="small", bits=80.0, bytes=10),
    ]
    assert micro_bpb(docs) == 180.0 / 110.0
    assert macro_bpb(docs) == (1.0 + 8.0) / 2.0
    assert domain_breakdown(docs)[0]["domain"] == "large"


def test_relative_gain() -> None:
    assert relative_gain(4.0, 3.0) == 0.25


def test_score_100_is_linear_and_higher_is_better() -> None:
    assert bpb_to_score_100(0.0) == 100.0
    assert bpb_to_score_100(8.0) == 50.0
    assert bpb_to_score_100(16.0) == 0.0
    assert bpb_to_score_100(4.0) == 75.0


def test_score_100_clips_outside_published_range() -> None:
    assert bpb_to_score_100(20.0) == 0.0
    with pytest.raises(ValueError):
        bpb_to_score_100(-1.0)
