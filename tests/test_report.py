from cbench.report import render_markdown


def _api_run(name: str, score: float) -> dict:
    return {
        "run_type": "api_track",
        "model": {
            "name": name,
            "access_tier": "black-box-chat-only",
            "reasoning_effort": "medium",
        },
        "scores": {
            "cbench_api_score": score,
            "score_100_ci_95": [score - 1, score + 1],
            "macro_accuracy": 0.75,
            "correct": 3,
            "cases": 4,
        },
    }


def test_report_ranks_only_api_track_runs() -> None:
    report = render_markdown(
        [
            _api_run("lower", 70.0),
            _api_run("higher", 90.0),
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
    assert "| Rank | Model | Setting | C-Bench API Score" in report
    assert report.index("| 1 | higher | medium | 90.000") < report.index(
        "| 2 | lower | medium | 70.000"
    )
    assert "| 3 | exact-model" not in report
    assert "Exact Compression Diagnostics" in report
    assert "| exact-model | hf_model | 1.000000 | 1.100000 |" in report


def test_report_escapes_untrusted_table_fields() -> None:
    run = _api_run("name|with\nline", 80.0)
    run["model"]["access_tier"] = "tier|one"
    run["run_type"] = "api_track"
    run["domain_breakdown"] = [
        {
            "domain": "domain|with\nline",
            "cases": 1,
            "answered": 1,
            "correct": 1,
            "accuracy": 1.0,
            "api_score_100": 100.0,
        }
    ]
    report = render_markdown([run])
    assert "| 1 | name\\|with line | medium |" in report
    assert "| domain\\|with line | 1 | 1 |" in report
    assert "tier\\|one" in report
