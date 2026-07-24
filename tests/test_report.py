import json
import math
from pathlib import Path

import pytest

from cbench.report import render_markdown, write_report


def _generation_run(name: str, score: float) -> dict:
    return {
        "run_type": "generation_track",
        "model": {
            "name": name,
            "access_tier": "black-box-chat-only",
            "reasoning_effort": "medium",
        },
        "scores": {
            "cbench_score": score,
            "score_100_ci_95": [score - 1, score + 1],
            "macro_similarity": 0.9,
            "macro_prefix": 0.75,
            "exact": 3,
            "cases": 4,
        },
    }


def test_report_ranks_only_generation_track_runs() -> None:
    report = render_markdown(
        [
            _generation_run("lower", 20.0),
            _generation_run("higher", 30.0),
            {
                "run_type": "api_track",
                "model": {"name": "choice-model"},
                "scores": {
                    "cbench_api_score": 99.0,
                    "macro_accuracy": 1.0,
                    "correct": 4,
                    "cases": 4,
                },
            },
            {
                "run_type": "hf_model",
                "model": {"name": "exact-model"},
                "scores": {
                    "score_100": 99.0,
                    "macro_bpb": 1.0,
                    "micro_bpb": 1.1,
                },
            },
        ]
    )
    assert "| Rank | Model | Setting | C-Bench Score" in report
    assert report.index("| 1 | higher | medium | 30.000") < report.index(
        "| 2 | lower | medium | 20.000"
    )
    assert "| 3 | choice-model" not in report
    assert "API Choice Diagnostics" in report
    assert "| 3 | exact-model" not in report
    assert "Exact Compression Diagnostics" in report
    assert "| exact-model | hf_model | 1.000000 | 1.100000 |" in report


def test_report_escapes_untrusted_table_fields() -> None:
    run = _generation_run("name|with\nline", 30.0)
    run["model"]["access_tier"] = "tier|one"
    run["domain_breakdown"] = [
        {
            "domain": "domain|with\nline",
            "cases": 1,
            "answered": 1,
            "cbench_score": 100.0,
            "similarity": 1.0,
            "prefix": 1.0,
            "exact": 1,
        }
    ]
    report = render_markdown([run])
    assert "| 1 | name\\|with line | medium |" in report
    assert "| domain\\|with line | 1 | 1 | 100.000000 |" in report
    assert "tier\\|one" in report


@pytest.mark.parametrize("score", [math.nan, math.inf, -1.0, 100.1])
def test_report_rejects_invalid_leaderboard_scores(score: float) -> None:
    with pytest.raises(ValueError, match="cbench_score"):
        render_markdown([_generation_run("invalid", score)])


def test_report_rejects_unknown_run_types() -> None:
    with pytest.raises(ValueError, match="unsupported run_type"):
        render_markdown([{"run_type": "mystery", "scores": {}}])


def test_report_only_flattens_baseline_collections(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(
        json.dumps(
            {
                "run_type": "generation_track",
                "runs": [_generation_run("nested", 50.0)],
                "scores": {"cbench_score": 50.0},
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "report.md"
    write_report([path], output)
    report = output.read_text(encoding="utf-8")
    assert "nested" not in report
    assert "| 1 | run | default | 50.000000 |" in report


def test_report_rejects_non_object_input(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected a JSON object"):
        write_report([path], tmp_path / "report.md")
