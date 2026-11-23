from __future__ import annotations

import csv
import hashlib
import json
from math import ceil
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
FIGURE_WIDTH = 7.2
ROW_HEIGHT = 0.43
HEADER_HEIGHT = 1.0
FOOTER_HEIGHT = 0.62
TITLE = "Official C-Bench rankings"


def load_rows() -> list[dict[str, str]]:
    with SOURCE_PATH.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError("leaderboard source data is empty")
    return sorted(rows, key=lambda row: float(row["cbench_score"]), reverse=True)


def plot(rows: list[dict[str, str]]) -> tuple[float, float]:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [
                "Arial",
                "Helvetica",
                "Liberation Sans",
                "DejaVu Sans",
            ],
            "axes.labelsize": 12,
            "xtick.labelsize": 11,
            "axes.linewidth": 0.7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "svg.fonttype": "none",
            "svg.hashsalt": "cbench-official-leaderboard",
            "pdf.fonttype": 42,
        }
    )

    plot_height = len(rows) * ROW_HEIGHT
    figure_height = HEADER_HEIGHT + plot_height + FOOTER_HEIGHT
    figure_size = (FIGURE_WIDTH, figure_height)
    figure = plt.figure(figsize=figure_size, facecolor="white")
    left_margin = 0.05
    axis = figure.add_axes(
        (left_margin, FOOTER_HEIGHT / figure_height, 0.90, plot_height / figure_height)
    )

    positions = list(reversed(range(len(rows))))
    scores = [float(row["cbench_score"]) for row in rows]
    score_limit = max(10, 10 * ceil(max(scores) / 10))
    text_position = axis.get_yaxis_transform()

    axis.barh(
        [position - 0.21 for position in positions],
        scores,
        height=0.17,
        color="#0F766E",
    )
    for row, position, score in zip(rows, positions, scores):
        axis.text(
            0,
            position + 0.17,
            f"{row['model']} ({row['setting']})",
            transform=text_position,
            color="#0F172A",
            fontsize=15,
            va="center",
        )
        axis.text(
            1,
            position + 0.17,
            f"{score:.2f}",
            transform=text_position,
            color="#0F172A",
            fontsize=15,
            fontweight="bold",
            ha="right",
            va="center",
        )

    axis.set_xlim(0, score_limit)
    axis.set_ylim(-0.55, len(rows) - 0.55)
    axis.set_yticks([])
    axis.set_xticks(range(0, score_limit + 1, 10))
    axis.set_xlabel("C-Bench Score / 100", color="#334155", labelpad=6)
    axis.tick_params(axis="x", colors="#475569", length=3)
    axis.spines["bottom"].set_color("#CBD5E1")

    figure.text(
        left_margin,
        1 - 0.25 / figure_height,
        TITLE,
        fontsize=23,
        fontweight="bold",
        color="#0F172A",
        va="top",
    )
    figure.text(
        left_margin,
        1 - 0.63 / figure_height,
        "Higher is better",
        fontsize=13,
        color="#475569",
        va="top",
    )
    figure.savefig(
        SVG_PATH,
        format="svg",
        metadata={"Date": None, "Title": TITLE},
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
            "Title": TITLE,
        },
    )
    figure.savefig(
        PNG_PATH,
        format="png",
        dpi=300,
        metadata={"Title": TITLE},
    )
    figure.savefig(
        TIFF_PATH,
        format="tiff",
        dpi=300,
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(figure)
    return figure_size


def write_qa(rows: list[dict[str, str]], figure_size: tuple[float, float]) -> None:
    with Image.open(PNG_PATH) as image:
        png_dimensions = list(image.size)
    qa = {
        "claim": f"{rows[0]['model']} leads the current {len(rows)}-entry official leaderboard.",
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
        "figure_size_inches": list(figure_size),
        "figure_width_mm": round(figure_size[0] * 25.4, 2),
        "png_dpi": 300,
        "python": platform.python_version(),
        "matplotlib": mpl.__version__,
        "private_data_included": False,
        "validation_notes": [
            "The 183 mm width matches a common double-column figure.",
            "Height grows with the number of ranked entries to preserve row spacing.",
            "Raster exports use 300 dpi for the README; vector exports remain editable.",
            "The validator's log-guard warning refers to the documented score "
            "formula; score inputs are validated by cbench.generation_track.",
        ],
    }
    QA_PATH.write_text(json.dumps(qa, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    figure_size = plot(rows)
    write_qa(rows, figure_size)
    print(f"Wrote {SVG_PATH.relative_to(ROOT)}")
    print(f"Wrote {PDF_PATH.relative_to(ROOT)}")
    print(f"Wrote {PNG_PATH.relative_to(ROOT)}")
    print(f"Wrote {TIFF_PATH.relative_to(ROOT)}")
    print(f"Wrote {QA_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
