from __future__ import annotations

import hashlib
import json
from pathlib import Path
import random

from cbench.data.manifest import load_suite_config
from cbench.data.validation import validate_suite


CONTEXT_CHARS = 600
CONTINUATION_CHARS = 80
DISTRACTOR_OFFSETS = (760, 920, 1080)


def extract_candidates(text: str, *, case_id: str) -> list[str]:
    candidates = [
        text[CONTEXT_CHARS : CONTEXT_CHARS + CONTINUATION_CHARS],
        *[
            text[offset : offset + CONTINUATION_CHARS]
            for offset in DISTRACTOR_OFFSETS
        ],
    ]
    if any(len(candidate) != CONTINUATION_CHARS for candidate in candidates):
        raise ValueError(f"{case_id}: document is too short for API cases")
    if len(set(candidates)) != len(candidates):
        raise ValueError(f"{case_id}: API candidates must be unique")
    return candidates


def main() -> None:
    config = load_suite_config("configs/public_dev.yaml")
    entries = validate_suite(config)
    cases = []
    for entry in entries:
        source_path = config.manifest_path.parent / entry.path
        text = source_path.read_text(encoding="utf-8")
        candidates = extract_candidates(text, case_id=entry.id)
        seed = int.from_bytes(
            hashlib.sha256(entry.id.encode()).digest()[:8],
            byteorder="big",
        )
        order = list(range(len(candidates)))
        random.Random(seed).shuffle(order)
        cases.append(
            {
                "id": entry.id,
                "domain": entry.domain,
                "context": text[:CONTEXT_CHARS],
                "candidates": [candidates[index] for index in order],
                "answer": order.index(0),
            }
        )

    output = Path("datasets/public_dev_api_cases.jsonl")
    output.write_text(
        "".join(
            json.dumps(case, ensure_ascii=False, separators=(",", ":")) + "\n"
            for case in cases
        ),
        encoding="utf-8",
    )
    print(f"Wrote {len(cases)} cases to {output}")


if __name__ == "__main__":
    main()
