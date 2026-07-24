import pytest

from scripts.build_public_api_cases import (
    CONTINUATION_CHARS,
    DISTRACTOR_OFFSETS,
    extract_candidates,
)


def test_api_case_builder_rejects_truncated_distractors() -> None:
    text = "x" * (DISTRACTOR_OFFSETS[-1] + CONTINUATION_CHARS - 1)
    with pytest.raises(ValueError, match="too short"):
        extract_candidates(text, case_id="short")
