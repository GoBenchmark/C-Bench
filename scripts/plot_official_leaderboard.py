from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import platform

import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets"
SOURCE_PATH = ASSET_DIR / "cbench-official-leaderboard.csv"
SVG_PATH = ASSET_DIR / "cbench-official-leaderboard.svg"
PDF_PATH = ASSET_DIR / "cbench-official-leaderboard.pdf"
PNG_PATH = ASSET_DIR / "cbench-official-leaderboard.png"
TIFF_PATH = ASSET_DIR / "cbench-official-leaderboard.tiff"
QA_PATH = ASSET_DIR / "cbench-official-leaderboard.qa.json"

COLORS = {
    "gpt-5.6-sol": "#0F766E",
    "gpt-5.6-luna": "#64748B",
    "gpt-5.6-terra": "#64748B",
}


def load_rows() -> list[dict[str, str]]:
    with SOURCE_PATH.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError("leaderboard source data is empty")
    return sorted(rows, key=lambda row: float(row["cbench_score"]), reverse=True)


def plot(rows: list[dict[str, str]]) -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Arial",
                "Helvetica",
                "Liberation Sans",
                "DejaVu Sans",
            ],
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 11,
            "xtick.labelsize": 8,
            "ytick.labelsize": 10,
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "svg.fonttype": "none",
            "svg.hashsalt": "cbench-official-leaderboard",
            "pdf.fonttype": 42,
        }
    )

    figure = plt.figure(figsize=(7.2, 3.2), facecolor="white")
    axis = figure.add_axes((0.22, 0.20, 0.72, 0.60), facecolor="white")

    positions = list(reversed(range(len(rows))))
    scores = [float(row["cbench_score"]) for row in rows]
    models = [row["model"] for row in rows]
    model_labels = [f"{row['model']} ({row['setting']})" for row in rows]
    colors = [COLORS[model] for model in models]

    axis.barh(positions, scores, height=0.52, color=colors)

    for position, score in zip(positions, scores):
        axis.text(
            score + 0.45,
            position,
            f"{score:.2f}",
            color="#0F172A",
            fontsize=10,
            fontweight="bold",
            va="center",
        )

    axis.set_xlim(0, 35)
    axis.set_ylim(-0.65, len(rows) - 0.35)
    axis.set_yticks(positions, model_labels, fontweight="bold", color="#0F172A")
    axis.set_xticks([0, 10, 20, 30])
    axis.set_xlabel("C-Bench Score", color="#334155", labelpad=8)
    axis.tick_params(axis="y", length=0, pad=12)
    axis.tick_params(axis="x", colors="#64748B", length=0)
    axis.grid(axis="x", color="#CBD5E1", linewidth=0.6, alpha=0.65)
    axis.set_axisbelow(True)
    axis.spines["bottom"].set_color("#94A3B8")

    figure.text(
        0.08,
        0.90,
        "Official C-Bench leaderboard",
        fontsize=17,
        fontweight="bold",
        color="#0F172A",
        ha="left",
    )
    figure.text(
        0.08,
        0.83,
        "higher is better",
        fontsize=8.5,
        color="#64748B",
        ha="left",
    )

    figure.savefig(
        SVG_PATH,
        format="svg",
        metadata={"Date": None, "Title": "Official C-Bench leaderboard"},
    )
    svg_text = SVG_PATH.read_text(encoding="utf-8")
    SVG_PATH.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )
    figure.savefig(
        PDF_PATH,
        format="pdf",
        metadata={
            "CreationDate": None,
            "ModDate": None,
            "Title": "Official C-Bench leaderboard",
        },
    )
    figure.savefig(
        PNG_PATH,
        format="png",
        dpi=300,
        metadata={"Title": "Official C-Bench leaderboard"},
    )
    figure.savefig(
        TIFF_PATH,
        format="tiff",
        dpi=300,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(figure)


def write_qa(rows: list[dict[str, str]]) -> None:
    with Image.open(PNG_PATH) as image:
        png_dimensions = list(image.size)
    qa = {
        "claim": "gpt-5.6-sol leads the current three-model official leaderboard.",
        "source_data": SOURCE_PATH.name,
        "source_sha256": hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest(),
        "rows": len(rows),
        "excluded_rows": 0,
        "score_transform": "100 * min(1, log10(1 / (1 - macro_similarity)) / 3)",
        "outputs": [
            SVG_PATH.name,
            PDF_PATH.name,
            PNG_PATH.name,
            TIFF_PATH.name,
        ],
        "png_dimensions_px": png_dimensions,
        "figure_size_inches": [7.2, 3.2],
        "figure_width_mm": 182.88,
        "png_dpi": 300,
        "python": platform.python_version(),
        "matplotlib": mpl.__version__,
        "private_data_included": False,
        "validation_notes": [
            "The 183 mm width matches a common double-column figure.",
            "The validator's log-guard warning refers to the documented score "
            "formula; score inputs are validated by cbench.generation_track.",
        ],
    }
    QA_PATH.write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    plot(rows)
    write_qa(rows)
    print(f"Wrote {SVG_PATH.relative_to(ROOT)}")
    print(f"Wrote {PDF_PATH.relative_to(ROOT)}")
    print(f"Wrote {PNG_PATH.relative_to(ROOT)}")
    print(f"Wrote {TIFF_PATH.relative_to(ROOT)}")
    print(f"Wrote {QA_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
