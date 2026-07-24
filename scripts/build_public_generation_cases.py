from __future__ import annotations

import json
from pathlib import Path

from cbench.data.manifest import load_suite_config
from cbench.data.validation import validate_suite


CONTEXT_CHARS = 600
TARGET_CHARS = 80


def main() -> None:
    config = load_suite_config("configs/public_dev.yaml")
    entries = validate_suite(config)
    cases = []
    for entry in entries:
        source_path = config.manifest_path.parent / entry.path
        text = source_path.read_text(encoding="utf-8")
        target = text[CONTEXT_CHARS : CONTEXT_CHARS + TARGET_CHARS]
        if len(target) != TARGET_CHARS:
            raise ValueError(f"{entry.id}: document is too short")
        cases.append(
            {
                "id": entry.id,
                "domain": entry.domain,
                "context": text[:CONTEXT_CHARS],
                "target": target,
            }
        )

    output = Path("datasets/public_dev_generation_cases.jsonl")
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
