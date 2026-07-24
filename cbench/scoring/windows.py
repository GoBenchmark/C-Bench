from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Window:
    context_ids: list[int]
    target_ids: list[int]
    target_start_absolute_token: int
    target_end_absolute_token: int


def make_windows(
    token_ids: list[int],
    max_context_tokens: int,
    target_chunk_tokens: int,
    *,
    use_bos: bool = False,
) -> list[Window]:
    if max_context_tokens <= 0:
        raise ValueError("max_context_tokens must be positive")
    if target_chunk_tokens <= 0:
        raise ValueError("target_chunk_tokens must be positive")
    if not token_ids:
        return []

    start = 0 if use_bos else 1
    windows: list[Window] = []
    while start < len(token_ids):
        end = min(len(token_ids), start + target_chunk_tokens)
        context_start = max(0, start - max_context_tokens)
        windows.append(
            Window(
                context_ids=token_ids[context_start:start],
                target_ids=token_ids[start:end],
                target_start_absolute_token=start,
                target_end_absolute_token=end,
            )
        )
        start = end
    return windows


def covered_target_indices(windows: list[Window]) -> list[int]:
    indices: list[int] = []
    for window in windows:
        indices.extend(range(window.target_start_absolute_token, window.target_end_absolute_token))
    return indices
