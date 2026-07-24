from cbench.report import render_markdown


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
