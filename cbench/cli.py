from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from cbench import __version__
from cbench.api_track import load_api_cases, load_api_predictions, score_api_track
from cbench.bootstrap import bootstrap_macro_bpb_ci
from cbench.compressors.baselines import run_baselines
from cbench.data.manifest import load_suite_config
from cbench.data.validation import validate_suite
from cbench.generation_track import (
    load_generation_cases,
    load_generation_predictions,
    score_generation_track,
)
from cbench.metrics import DocumentScore, aggregate_scores, domain_breakdown
from cbench.providers.capabilities import (
    api_track_model_metadata,
    canonical_model_metadata,
)
from cbench.report import write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cbench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a suite manifest")
    validate_parser.add_argument("--suite", required=True)

    collect_parser = subparsers.add_parser("collect", help="Build a dataset from a locked source catalog")
    collect_parser.add_argument("--catalog", required=True)
    collect_parser.add_argument("--output-dir", required=True)
    collect_parser.add_argument("--manifest", required=True)
    collect_parser.add_argument("--force", action="store_true")

    baseline_parser = subparsers.add_parser("baseline", help="Run classical compressor baselines")
    baseline_parser.add_argument("--suite", required=True)
    baseline_parser.add_argument("--compressors", default="gzip,zstd,brotli,xz")
    baseline_parser.add_argument("--output", required=True)

    score_parser = subparsers.add_parser("score", help="Score a Hugging Face causal LM")
    score_parser.add_argument("--model", required=True)
    score_parser.add_argument("--suite", required=True)
    score_parser.add_argument("--max-context-tokens", type=int, default=1024)
    score_parser.add_argument("--target-chunk-tokens", type=int, default=256)
    score_parser.add_argument("--output", required=True)
    score_parser.add_argument("--allow-invalid-utf8", action="store_true")
    score_parser.add_argument("--use-bos", action="store_true")
    score_parser.add_argument("--device")

    api_score_parser = subparsers.add_parser(
        "api-score",
        help="Score black-box model choices for the C-Bench API Track",
    )
    api_score_parser.add_argument("--cases", required=True)
    api_score_parser.add_argument("--predictions", required=True)
    api_score_parser.add_argument("--suite", required=True)
    api_score_parser.add_argument("--model", required=True)
    api_score_parser.add_argument("--reasoning-effort")
    api_score_parser.add_argument("--output", required=True)

    generation_score_parser = subparsers.add_parser(
        "generation-score",
        help="Calculate the main C-Bench Score from generated continuations",
    )
    generation_score_parser.add_argument("--cases", required=True)
    generation_score_parser.add_argument("--predictions", required=True)
    generation_score_parser.add_argument("--suite", required=True)
    generation_score_parser.add_argument("--model", required=True)
    generation_score_parser.add_argument("--reasoning-effort")
    generation_score_parser.add_argument("--output", required=True)

    report_parser = subparsers.add_parser("report", help="Generate Markdown report")
    report_parser.add_argument("--inputs", nargs="+", required=True)
    report_parser.add_argument("--output", required=True)

    args = parser.parse_args(argv)
    if args.command == "validate":
        return _cmd_validate(args)
    if args.command == "collect":
        return _cmd_collect(args)
    if args.command == "baseline":
        return _cmd_baseline(args)
    if args.command == "score":
        return _cmd_score(args)
    if args.command == "api-score":
        return _cmd_api_score(args)
    if args.command == "generation-score":
        return _cmd_generation_score(args)
    if args.command == "report":
        return _cmd_report(args)
    raise AssertionError(f"Unhandled command {args.command}")


def _cmd_validate(args: argparse.Namespace) -> int:
    config = load_suite_config(args.suite)
    entries = validate_suite(config)
    print(f"Validated {len(entries)} entries for suite {config.name}")
    return 0


def _cmd_collect(args: argparse.Namespace) -> int:
    from cbench.data.collection import collect_catalog

    rows = collect_catalog(
        args.catalog,
        args.output_dir,
        args.manifest,
        force=args.force,
    )
    print(f"Collected {len(rows)} documents into {args.output_dir}")
    print(f"Wrote {args.manifest}")
    return 0


def _cmd_baseline(args: argparse.Namespace) -> int:
    config = load_suite_config(args.suite)
    entries = validate_suite(config)
    compressors = [item.strip() for item in args.compressors.split(",") if item.strip()]
    documents, warnings = run_baselines(entries, config.manifest_path, compressors)

    runs: list[dict[str, Any]] = []
    for compressor in compressors:
        rows = [row for row in documents if row["compressor"] == compressor]
        if not rows:
            continue
        doc_scores = [
            DocumentScore(
                id=str(row["id"]),
                domain=str(row["domain"]),
                bits=float(row["bits"]),
                bytes=int(row["raw_bytes"]),
            )
            for row in rows
        ]
        runs.append(
            {
                "benchmark_version": f"cbench-{__version__}",
                "run_type": "baseline",
                "suite": config.name,
                "compressor": compressor,
                "scores": aggregate_scores(doc_scores, bootstrap_ci=bootstrap_macro_bpb_ci(doc_scores, samples=200)),
                "domain_breakdown": domain_breakdown(doc_scores),
                "documents": rows,
                "warnings": [warning for warning in warnings if compressor in warning],
            }
        )

    output = {
        "benchmark_version": f"cbench-{__version__}",
        "run_type": "baseline_collection",
        "suite": config.name,
        "compressors": compressors,
        "runs": runs,
        "warnings": warnings,
    }
    _write_json(args.output, output)
    for warning in warnings:
        print(warning)
    print(f"Wrote {args.output}")
    return 0


def _cmd_score(args: argparse.Namespace) -> int:
    if not args.model.startswith("hf:"):
        raise SystemExit("Only hf:<model-name-or-path> is supported for exact scoring")
    from cbench.scoring.hf_causal import score_hf_entries

    config = load_suite_config(args.suite)
    entries = validate_suite(config)
    model_name = args.model.removeprefix("hf:")
    results, resources = score_hf_entries(
        model_name,
        entries,
        config.manifest_path,
        max_context_tokens=args.max_context_tokens,
        target_chunk_tokens=args.target_chunk_tokens,
        allow_invalid_utf8=args.allow_invalid_utf8,
        use_bos=args.use_bos,
        device=args.device,
    )
    doc_scores = [result.score for result in results]
    documents = []
    for result in results:
        row = result.score.as_dict()
        row["scored_tokens"] = result.scored_tokens
        row["unscored_initial_tokens"] = result.unscored_initial_tokens
        documents.append(row)
    output = {
        "benchmark_version": f"cbench-{__version__}",
        "run_type": "hf_model",
        "suite": config.name,
        "model": canonical_model_metadata(name=model_name, access_tier="open-local-logits"),
        "scores": aggregate_scores(doc_scores, bootstrap_ci=bootstrap_macro_bpb_ci(doc_scores, samples=200)),
        "domain_breakdown": domain_breakdown(doc_scores),
        "documents": documents,
        "resources": resources,
        "settings": {
            "max_context_tokens": args.max_context_tokens,
            "target_chunk_tokens": args.target_chunk_tokens,
            "allow_invalid_utf8": args.allow_invalid_utf8,
            "use_bos": args.use_bos,
        },
    }
    _write_json(args.output, output)
    print(f"Wrote {args.output}")
    return 0


def _cmd_api_score(args: argparse.Namespace) -> int:
    cases = load_api_cases(args.cases)
    predictions = load_api_predictions(args.predictions)
    scored = score_api_track(cases, predictions)
    output = {
        "benchmark_version": f"cbench-{__version__}",
        "run_type": "api_track",
        "suite": args.suite,
        "model": api_track_model_metadata(
            name=args.model,
            access_tier="black-box-chat-only",
            reasoning_effort=args.reasoning_effort,
        ),
        "scores": scored["scores"],
        "domain_breakdown": scored["domain_breakdown"],
        "results": scored["results"],
        "settings": {
            "candidate_count": scored["scores"]["candidate_count"],
            "tools": "disabled",
            "retrieval": "disabled",
        },
    }
    _write_json(args.output, output)
    print(
        f"C-Bench API Score: {scored['scores']['cbench_api_score']:.2f} "
        f"({scored['scores']['correct']}/{scored['scores']['cases']} correct)"
    )
    print(f"Wrote {args.output}")
    return 0


def _cmd_generation_score(args: argparse.Namespace) -> int:
    cases = load_generation_cases(args.cases)
    predictions = load_generation_predictions(args.predictions)
    scored = score_generation_track(cases, predictions)
    output = {
        "benchmark_version": f"cbench-{__version__}",
        "run_type": "generation_track",
        "suite": args.suite,
        "model": api_track_model_metadata(
            name=args.model,
            access_tier="black-box-chat-only",
            reasoning_effort=args.reasoning_effort,
        ),
        "scores": scored["scores"],
        "domain_breakdown": scored["domain_breakdown"],
        "results": scored["results"],
        "settings": {
            "similarity": "difflib.SequenceMatcher over UTF-8 bytes",
            "score_nines": scored["scores"]["score_nines"],
            "tools": "disabled",
            "retrieval": "disabled",
        },
    }
    _write_json(args.output, output)
    print(
        f"C-Bench Score: {scored['scores']['cbench_score']:.2f} "
        f"(similarity {scored['scores']['macro_similarity']:.3%})"
    )
    print(f"Wrote {args.output}")
    return 0


def _cmd_report(args: argparse.Namespace) -> int:
    write_report(args.inputs, args.output)
    print(f"Wrote {args.output}")
    return 0


def _write_json(path: str | Path, data: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
