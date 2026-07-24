from cbench.report import render_markdown


def test_report_ranks_by_cbench_score_descending() -> None:
    report = render_markdown(
        [
            {
                "run_type": "model",
                "model": {"name": "lower"},
                "scores": {"score_100": 70.0, "macro_bpb": 4.8, "micro_bpb": 4.9},
            },
            {
                "run_type": "model",
                "model": {"name": "higher"},
                "scores": {"score_100": 90.0, "macro_bpb": 1.6, "micro_bpb": 1.7},
            },
        ]
    )
    assert "| Rank | Run | Type | C-Bench Score" in report
    assert report.index("| 1 | higher | model | 90.000") < report.index("| 2 | lower | model | 70.000")


def test_report_escapes_untrusted_table_fields() -> None:
    report = render_markdown(
        [
            {
                "run_type": "model|run",
                "model": {"name": "name|with\nline", "access_tier": "tier|one"},
                "scores": {"score_100": 80.0},
                "domain_breakdown": [{"domain": "domain|with\nline", "documents": 1, "bytes": 4, "score_100": 80.0, "bpb": 3.2}],
            }
        ]
    )
    assert "| 1 | name\\|with line | model\\|run |" in report
    assert "| domain\\|with line | 1 | 4 |" in report
    assert "tier\\|one" in report
