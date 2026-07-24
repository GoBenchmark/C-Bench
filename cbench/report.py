from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cbench.metrics import bpb_to_score_100


def load_run(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def render_markdown(runs: list[dict[str, Any]]) -> str:
    lines = ["# C-Bench Report", ""]
    if not runs:
        lines.append("No runs supplied.")
        return "\n".join(lines) + "\n"

    ordered_runs = _sort_runs(runs)

    lines.extend(
        [
            "## Summary",
            "",
            "> C-Bench Score is 0-100, higher is better. BPB remains the audit metric.",
            "",
            "| Rank | Run | Type | C-Bench Score ↑ | Score 95% CI | Macro BPB ↓ | Micro BPB ↓ | Notes |",
            "|---:|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for rank, run in enumerate(ordered_runs, start=1):
        run_type = run.get("run_type", "unknown")
        suite = run.get("suite", "")
        label = run.get("model", {}).get("name") or run.get("compressor") or suite or "run"
        scores = run.get("scores", {})
        score = scores.get("score_100")
        if score is None and scores.get("macro_bpb") is not None:
            score = bpb_to_score_100(float(scores["macro_bpb"]))
        score_ci = scores.get("score_100_ci_95")
        if score_ci is None and scores.get("bootstrap_ci_95"):
            bpb_ci = scores["bootstrap_ci_95"]
            score_ci = [bpb_to_score_100(float(bpb_ci[1])), bpb_to_score_100(float(bpb_ci[0]))]
        macro = scores.get("macro_bpb")
        micro = scores.get("micro_bpb")
        notes = run.get("model", {}).get("access_tier") or ""
        lines.append(
            f"| {rank} | {_fmt(label)} | {_fmt(run_type)} | {_fmt(score)} | {_fmt_ci(score_ci)} "
            f"| {_fmt(macro)} | {_fmt(micro)} | {_fmt(notes)} |"
        )

    for run in ordered_runs:
        label = run.get("model", {}).get("name") or run.get("compressor") or run.get("suite", "run")
        lines.extend(["", f"## {_heading(label)}", ""])
        if run.get("domain_breakdown"):
            lines.extend(["| Domain | Documents | Bytes | Score ↑ | BPB ↓ |", "|---|---:|---:|---:|---:|"])
            for row in run["domain_breakdown"]:
                lines.append(
                    f"| {_fmt(row['domain'])} | {row.get('documents', '')} | {row.get('bytes', '')} "
                    f"| {_fmt(row.get('score_100', bpb_to_score_100(float(row['bpb']))))} "
                    f"| {_fmt(row.get('bpb'))} |"
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


def _sort_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(run: dict[str, Any]) -> tuple[bool, float]:
        scores = run.get("scores", {})
        score = scores.get("score_100")
        if score is None and scores.get("macro_bpb") is not None:
            score = bpb_to_score_100(float(scores["macro_bpb"]))
        return (score is not None, float(score) if score is not None else 0.0)

    return sorted(runs, key=sort_key, reverse=True)
