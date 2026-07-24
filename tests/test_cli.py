from pathlib import Path

import pytest

from cbench.cli import main


def test_baseline_rejects_empty_compressor_selection(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="at least one compressor"):
        main(
            [
                "baseline",
                "--suite",
                "unused.yaml",
                "--compressors",
                ",",
                "--output",
                str(tmp_path / "baseline.json"),
            ]
        )
