from __future__ import annotations

import csv
import hashlib
from io import BytesIO
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
HEADER_ART_PATH = ASSET_DIR / "cbench-leaderboard-ribbons.png"
FIGURE_WIDTH = 7.2
WEB_PNG_DPI = 240
ROW_HEIGHT = 0.38
HEADER_HEIGHT = 0.96
FOOTER_HEIGHT = 0.62
TITLE = "Official C-Bench rankings"
PAPER = "#FBF6EE"
INK = "#191624"
RULE = "#DFD3C6"
BAR_COLORS = {"gpt": "#3155C3", "claude": "#AE471E"}


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
    figure = plt.figure(figsize=figure_size, facecolor=PAPER)
    left_margin = 0.05
    axis = figure.add_axes(
        (left_margin, FOOTER_HEIGHT / figure_height, 0.90, plot_height / figure_height),
        facecolor=PAPER,
    )

    positions = list(reversed(range(len(rows))))
    scores = [float(row["cbench_score"]) for row in rows]
    score_limit = max(10, 10 * ceil(max(scores) / 10))
    bar_left, bar_right = 0.43, 0.85
    score_scale = (bar_right - bar_left) / score_limit
    tick_positions = list(range(0, score_limit + 1, 10))

    axis.hlines(
        [position - 0.5 for position in positions] + [positions[0] + 0.5],
        0,
        1,
        colors=RULE,
        linewidth=0.45,
        zorder=0.5,
    )
    axis.vlines(
        [bar_left + tick * score_scale for tick in tick_positions],
        -0.5,
        len(rows) - 0.5,
        colors=RULE,
        linewidth=0.45,
        zorder=0.5,
    )
    colors = [BAR_COLORS[row["model"].split("-", 1)[0]] for row in rows]
    axis.barh(
        positions,
        [score * score_scale for score in scores],
        left=bar_left,
        height=0.46,
        color=colors,
    )

    for row, position, score in zip(rows, positions, scores):
        axis.text(
            0,
            position,
            f"{row['model']} ({row['setting']})",
            color=INK,
            fontsize=13.3,
            va="center",
        )
        axis.text(
            1,
            position,
            f"{score:.2f}",
            color=INK,
            fontsize=13.3,
            fontweight="bold",
            ha="right",
            va="center",
        )

    axis.set_xlim(0, 1)
    axis.set_ylim(-0.5, len(rows) - 0.5)
    axis.set_yticks([])
    axis.set_xticks([bar_left + tick * score_scale for tick in tick_positions], tick_positions)
    axis.set_xlabel(
        "C-Bench Score / 100",
        color=INK,
        labelpad=6,
        x=(bar_left + bar_right) / 2,
    )
    axis.tick_params(axis="x", colors="#594E51", length=0, pad=5)
    axis.spines["bottom"].set_visible(False)

    figure.text(
        left_margin,
        1 - 0.22 / figure_height,
        TITLE,
        fontfamily="serif",
        fontsize=24,
        fontweight="bold",
        color=INK,
        va="top",
    )
    figure.text(
        left_margin,
        1 - 0.60 / figure_height,
        "Higher is better",
        fontsize=11,
        color="#594E51",
        va="top",
    )
    art_axis = figure.add_axes(
        (0.76, 1 - 0.81 / figure_height, 0.19, 0.67 / figure_height),
        frameon=False,
    )
    art_axis.imshow(mpl.image.imread(HEADER_ART_PATH))
    art_axis.set_axis_off()
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
    with BytesIO() as png_buffer:
        figure.savefig(png_buffer, format="png", dpi=WEB_PNG_DPI)
        png_buffer.seek(0)
        with Image.open(png_buffer) as image:
            web_image = image.convert("RGB").quantize(
                colors=256, dither=Image.Dither.NONE
            )
            web_image.save(PNG_PATH, optimize=True, dpi=(WEB_PNG_DPI, WEB_PNG_DPI))
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
        "header_art": HEADER_ART_PATH.name,
        "header_art_source": "ImageGen",
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
        "png_dpi": WEB_PNG_DPI,
        "png_bytes": PNG_PATH.stat().st_size,
        "python": platform.python_version(),
        "matplotlib": mpl.__version__,
        "private_data_included": False,
        "validation_notes": [
            "The 183 mm width matches a common double-column figure.",
            "Height grows with the number of ranked entries to preserve row spacing.",
            "The README uses an optimized indexed PNG; TIFF is exported at 300 dpi.",
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
