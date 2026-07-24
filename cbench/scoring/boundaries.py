from __future__ import annotations


DEFAULT_TARGET_DELIMITER = "\n<CBENCH_TARGET>\n"


def join_context_target(context: str, target: str, delimiter: str = DEFAULT_TARGET_DELIMITER) -> str:
    return f"{context}{delimiter}{target}"
