import pytest

from cbench.bootstrap import bootstrap_macro_bpb_ci
from cbench.metrics import DocumentScore


def test_bootstrap_confidence_must_be_between_zero_and_one() -> None:
    documents = [DocumentScore(id="doc", domain="prose", bits=8.0, bytes=1)]
    with pytest.raises(ValueError, match="confidence"):
        bootstrap_macro_bpb_ci(documents, confidence=1.0)
