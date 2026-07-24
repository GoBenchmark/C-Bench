import pytest

from cbench.bootstrap import bootstrap_macro_bpb_ci
from cbench.metrics import DocumentScore


def test_bootstrap_confidence_must_be_between_zero_and_one() -> None:
    documents = [DocumentScore(id="doc", domain="prose", bits=8.0, bytes=1)]
    with pytest.raises(ValueError, match="confidence"):
        bootstrap_macro_bpb_ci(documents, confidence=1.0)


def test_bootstrap_preserves_every_domain() -> None:
    documents = [
        DocumentScore(id="a", domain="low", bits=1.0, bytes=1),
        DocumentScore(id="b", domain="high", bits=9.0, bytes=1),
    ]
    assert bootstrap_macro_bpb_ci(documents, samples=50, seed=7) == (5.0, 5.0)
