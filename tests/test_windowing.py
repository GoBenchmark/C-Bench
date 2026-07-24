from cbench.scoring.windows import covered_target_indices, make_windows
import pytest


def test_windows_cover_every_target_token_once_without_bos() -> None:
    windows = make_windows(list(range(10)), max_context_tokens=3, target_chunk_tokens=2)
    assert covered_target_indices(windows) == list(range(1, 10))


def test_windows_respect_context_cap() -> None:
    windows = make_windows(list(range(8)), max_context_tokens=2, target_chunk_tokens=3)
    assert all(len(window.context_ids) <= 2 for window in windows)
    assert windows[1].context_ids == [2, 3]


def test_zero_context_cap_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        make_windows([1, 2, 3], max_context_tokens=0, target_chunk_tokens=2)
