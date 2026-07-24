from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_run(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def render_markdown(runs: list[dict[str, Any]]) -> str:
    lines = ["# C-Bench Report", ""]
    if not runs:
        lines.append("No runs supplied.")
        return "\n".join(lines) + "\n"

    api_runs = _sort_api_runs(
        [run for run in runs if run.get("run_type") == "api_track"]
    )
    exact_runs = [run for run in runs if run.get("run_type") != "api_track"]

    lines.extend(
        [
            "## API Track Leaderboard",
            "",
            "> C-Bench API Score is 0-100 and chance-adjusted. Higher is better.",
            "",
            "| Rank | Model | Setting | C-Bench API Score ↑ | Score 95% CI | Macro accuracy ↑ | Correct | Notes |",
            "|---:|---|---|---:|---:|---:|---:|---|",
        ]
    )
    if not api_runs:
        lines.append("| - | No API Track runs supplied | - | - | - | - | - | - |")
    for rank, run in enumerate(api_runs, start=1):
        model = run.get("model", {})
        label = model.get("name") or run.get("suite") or "run"
        setting = model.get("reasoning_effort") or "default"
        scores = run.get("scores", {})
        score = scores.get("cbench_api_score")
        score_ci = scores.get("score_100_ci_95")
        macro_accuracy = scores.get("macro_accuracy")
        correct = f"{scores.get('correct', 0)}/{scores.get('cases', 0)}"
        notes = model.get("access_tier") or ""
        lines.append(
            f"| {rank} | {_fmt(label)} | {_fmt(setting)} | {_fmt(score)} "
            f"| {_fmt_ci(score_ci)} | {_fmt(macro_accuracy)} | {_fmt(correct)} "
            f"| {_fmt(notes)} |"
        )

    for run in api_runs:
        label = run.get("model", {}).get("name") or run.get("suite", "run")
        lines.extend(["", f"## {_heading(label)}", ""])
        if run.get("domain_breakdown"):
            lines.extend(
                [
                    "| Domain | Cases | Answered | Correct | Accuracy ↑ | API Score ↑ |",
                    "|---|---:|---:|---:|---:|---:|",
                ]
            )
            for row in run["domain_breakdown"]:
                lines.append(
                    f"| {_fmt(row['domain'])} | {_fmt(row.get('cases'))} "
                    f"| {_fmt(row.get('answered'))} | {_fmt(row.get('correct'))} "
                    f"| {_fmt(row.get('accuracy'))} | {_fmt(row.get('api_score_100'))} |"
                )

    if exact_runs:
        lines.extend(
            [
                "",
                "## Exact Compression Diagnostics",
                "",
                "These BPB results are retained for research and auditing. They are not "
                "leaderboard entries.",
                "",
                "| Run | Type | Macro BPB ↓ | Micro BPB ↓ | Access |",
                "|---|---|---:|---:|---|",
            ]
        )
        for run in exact_runs:
            label = (
                run.get("model", {}).get("name")
                or run.get("compressor")
                or run.get("suite", "run")
            )
            scores = run.get("scores", {})
            lines.append(
                f"| {_fmt(label)} | {_fmt(run.get('run_type', 'unknown'))} "
                f"| {_fmt(scores.get('macro_bpb'))} | {_fmt(scores.get('micro_bpb'))} "
                f"| {_fmt(run.get('model', {}).get('access_tier', ''))} |"
            )
    return "\n".join(lines) + "\n"


def write_report(input_paths: list[str | Path], output_path: str | Path) -> None:
    runs: list[dict[str, Any]] = []
    for path in input_paths:
        run = load_run(path)
        if isinstance(run.get("runs"), list):
            runs.extend(run["runs"])
        else:
            runs.append(run)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_markdown(runs), encoding="utf-8")


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return _escape_cell(str(value))


def _fmt_ci(value: Any) -> str:
    if not value:
        return "n/a"
    return f"{float(value[0]):.3f}-{float(value[1]):.3f}"


def _escape_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _heading(value: Any) -> str:
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def _sort_api_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(run: dict[str, Any]) -> tuple[bool, float]:
        scores = run.get("scores", {})
        score = scores.get("cbench_api_score")
        return (score is not None, float(score) if score is not None else 0.0)

    return sorted(runs, key=sort_key, reverse=True)
