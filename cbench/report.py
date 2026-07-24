from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


SUPPORTED_RUN_TYPES = {"generation_track", "api_track", "hf_model", "baseline"}


def load_run(path: str | Path) -> dict[str, Any]:
    run = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(run, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return run


def render_markdown(runs: list[dict[str, Any]]) -> str:
    lines = ["# C-Bench Report", ""]
    if not runs:
        lines.append("No runs supplied.")
        return "\n".join(lines) + "\n"
    _validate_runs(runs)

    generation_runs = _sort_generation_runs(
        [run for run in runs if run.get("run_type") == "generation_track"]
    )
    api_runs = _sort_api_runs(
        [run for run in runs if run.get("run_type") == "api_track"]
    )
    exact_runs = [
        run for run in runs if run.get("run_type") in {"hf_model", "baseline"}
    ]

    lines.extend(
        [
            "## C-Bench Leaderboard",
            "",
            "> C-Bench Score is a 0-100 log-scaled macro continuation-similarity "
            "score. Higher is better.",
            "",
            "| Rank | Model | Setting | C-Bench Score ↑ | Score 95% CI | "
            "Similarity ↑ | Prefix ↑ | Exact | Notes |",
            "|---:|---|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    if not generation_runs:
        lines.append(
            "| - | No generation-track runs supplied | - | - | - | - | - | - | - |"
        )
    for rank, run in enumerate(generation_runs, start=1):
        model = run.get("model", {})
        label = model.get("name") or run.get("suite") or "run"
        setting = model.get("reasoning_effort") or "default"
        scores = run.get("scores", {})
        exact = f"{scores.get('exact', 0)}/{scores.get('cases', 0)}"
        lines.append(
            f"| {rank} | {_fmt(label)} | {_fmt(setting)} "
            f"| {_fmt(scores.get('cbench_score'))} "
            f"| {_fmt_ci(scores.get('score_100_ci_95'))} "
            f"| {_fmt(scores.get('macro_similarity'))} "
            f"| {_fmt(scores.get('macro_prefix'))} | {_fmt(exact)} "
            f"| {_fmt(model.get('access_tier') or '')} |"
        )

    for run in generation_runs:
        label = run.get("model", {}).get("name") or run.get("suite", "run")
        lines.extend(["", f"## {_heading(label)}", ""])
        if run.get("domain_breakdown"):
            lines.extend(
                [
                    "| Domain | Cases | Answered | C-Bench Score ↑ | "
                    "Similarity ↑ | Prefix ↑ | Exact |",
                    "|---|---:|---:|---:|---:|---:|---:|",
                ]
            )
            for row in run["domain_breakdown"]:
                lines.append(
                    f"| {_fmt(row['domain'])} | {_fmt(row.get('cases'))} "
                    f"| {_fmt(row.get('answered'))} "
                    f"| {_fmt(row.get('cbench_score'))} "
                    f"| {_fmt(row.get('similarity'))} "
                    f"| {_fmt(row.get('prefix'))} | {_fmt(row.get('exact'))} |"
                )

    if api_runs:
        lines.extend(
            [
                "",
                "## API Choice Diagnostics",
                "",
                "These four-choice results are retained as supporting diagnostics. "
                "They are not leaderboard entries.",
                "",
                "| Model | Setting | API Score ↑ | Macro accuracy ↑ | Correct | Notes |",
                "|---|---|---:|---:|---:|---|",
            ]
        )
    for run in api_runs:
        model = run.get("model", {})
        scores = run.get("scores", {})
        correct = f"{scores.get('correct', 0)}/{scores.get('cases', 0)}"
        lines.append(
            f"| {_fmt(model.get('name') or run.get('suite') or 'run')} "
            f"| {_fmt(model.get('reasoning_effort') or 'default')} "
            f"| {_fmt(scores.get('cbench_api_score'))} "
            f"| {_fmt(scores.get('macro_accuracy'))} "
            f"| {_fmt(correct)} "
            f"| {_fmt(model.get('access_tier') or '')} |"
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
        if run.get("run_type") == "baseline_collection":
            if not isinstance(run.get("runs"), list):
                raise ValueError(f"{path}: baseline collection must contain a runs list")
            if not all(isinstance(item, dict) for item in run["runs"]):
                raise ValueError(f"{path}: 'runs' must contain JSON objects")
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


def _validate_runs(runs: list[dict[str, Any]]) -> None:
    for index, run in enumerate(runs, start=1):
        if not isinstance(run, dict):
            raise ValueError(f"run {index} must be a JSON object")
        run_type = run.get("run_type")
        if run_type not in SUPPORTED_RUN_TYPES:
            raise ValueError(f"run {index} has unsupported run_type: {run_type!r}")
        model = run.get("model")
        if model is not None and not isinstance(model, dict):
            raise ValueError(f"run {index} model must be a JSON object")
        scores = run.get("scores")
        if not isinstance(scores, dict):
            raise ValueError(f"run {index} must contain a scores object")
        if run_type == "generation_track":
            _score_value(
                scores.get("cbench_score"),
                f"run {index} cbench_score",
                maximum=100.0,
            )
        elif run_type == "api_track":
            _score_value(
                scores.get("cbench_api_score"),
                f"run {index} cbench_api_score",
                maximum=100.0,
            )
        else:
            _score_value(scores.get("macro_bpb"), f"run {index} macro_bpb")
            _score_value(scores.get("micro_bpb"), f"run {index} micro_bpb")


def _score_value(value: Any, label: str, *, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    if number < 0 or (maximum is not None and number > maximum):
        bounds = f" between 0 and {maximum:g}" if maximum is not None else " non-negative"
        raise ValueError(f"{label} must be{bounds}")
    return number


def _sort_api_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(run: dict[str, Any]) -> tuple[bool, float]:
        scores = run.get("scores", {})
        score = scores.get("cbench_api_score")
        return (score is not None, float(score) if score is not None else 0.0)

    return sorted(runs, key=sort_key, reverse=True)


def _sort_generation_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(run: dict[str, Any]) -> tuple[bool, float]:
        score = run.get("scores", {}).get("cbench_score")
        return (score is not None, float(score) if score is not None else 0.0)

    return sorted(runs, key=sort_key, reverse=True)
