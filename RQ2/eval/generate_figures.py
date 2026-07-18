"""
generate_figures.py
-------------------
Generates the three data-driven figures for the thesis:

    fig_method_comparison.pdf   — Micro-F1 and micro-IC by method and domain
    fig_distributions.pdf       — Constraint category distribution by domain
    fig_hallucination.pdf       — Hallucination rate by method and domain

Place this file at:
    RQ2/eval/generate_figures.py

Run from the project root:
    python RQ2/eval/generate_figures.py

Output PDFs are written to:
    RQ2/eval/results/figures/

Create the RQ2/eval/results/figures/ directory if it does not exist.
After running, upload the three PDFs to Overleaf under figures/ and replace
the \\fbox placeholder blocks in main.tex with:

    \\includegraphics[width=\\textwidth]{figures/fig_method_comparison}
    \\includegraphics[width=\\textwidth]{figures/fig_distributions}
    \\includegraphics[width=0.85\\textwidth]{figures/fig_hallucination}
"""

import json
import os
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless — no display required
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Paths ─────────────────────────────────────────────────────────────────────
# This script lives at RQ2/eval/generate_figures.py
# so the project root is two levels up.
SCRIPT_DIR   = Path(__file__).resolve().parent            # RQ2/eval/
PROJECT_ROOT = SCRIPT_DIR.parent.parent                   # project root

COMPARISONS  = PROJECT_ROOT / "RQ2" / "eval" / "results" / "comparisons"
GOLD_DIR     = PROJECT_ROOT / "annotations" / "gold-annotations"
OUTPUT_DIR   = PROJECT_ROOT / "RQ2" / "eval" / "results" / "figures"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
# Greyscale-friendly palette — readable in print and on screen
COLORS = {
    "travel":     "#2C5F8A",   # dark blue
    "healthcare": "#6B9E5E",   # muted green
    "bar_f1":     "#2C5F8A",
    "bar_ic":     "#A8C5DA",
    "methods_order": ["Zero-shot", "Few-shot", "CoT", "Hybrid"],
    "method_keys":   ["zeroshot", "fewshot", "cot", "hybrid"],
}

LABEL_MAP = {
    "zeroshot": "Zero-shot",
    "fewshot":  "Few-shot",
    "cot":      "CoT",
    "hybrid":   "Hybrid",
}

CATEGORY_ORDER = ["Temporal", "Spatial", "Logical", "Domain-default"]
CATEGORY_COLORS = ["#2C5F8A", "#6B9E5E", "#C4813A", "#8B5EA3"]

plt.rcParams.update({
    "font.family":      "serif",
    "font.size":        10,
    "axes.titlesize":   11,
    "axes.labelsize":   10,
    "xtick.labelsize":  9,
    "ytick.labelsize":  9,
    "legend.fontsize":  9,
    "figure.dpi":       150,
    "savefig.dpi":      300,
    "savefig.bbox":     "tight",
    "savefig.pad_inches": 0.05,
})


# ── Data loading ──────────────────────────────────────────────────────────────
def load_comparison(domain: str) -> dict:
    """Load method comparison JSON for a given domain."""
    path = COMPARISONS / f"{domain}_method_comparison.json"
    with open(path) as f:
        return json.load(f)


def load_gold(domain_fname: str) -> list:
    """Load gold annotation file and return flat list of constraint dicts."""
    path = GOLD_DIR / domain_fname
    with open(path) as f:
        data = json.load(f)
    return [c for a in data["annotations"] for c in a["constraints"]]


# ── Figure 1: Method Comparison ───────────────────────────────────────────────
def make_method_comparison():
    """
    Grouped bar chart: Micro-F1 and micro-IC for each method,
    Travel and Healthcare side by side in a 1x2 subplot layout.
    """
    travel_data     = load_comparison("travel")
    healthcare_data = load_comparison("healthcare")

    method_keys  = COLORS["method_keys"]
    method_labels = COLORS["methods_order"]

    def extract(comp_data):
        rows = {m["method"]: m["aggregate_metrics"] for m in comp_data["methods"]}
        f1   = [rows[k]["micro_f1"]                 for k in method_keys]
        ic   = [rows[k]["micro_intent_completeness"] for k in method_keys]
        return f1, ic

    t_f1, t_ic = extract(travel_data)
    h_f1, h_ic = extract(healthcare_data)

    x     = np.arange(len(method_labels))
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
    fig.subplots_adjust(wspace=0.12)

    for ax, f1_vals, ic_vals, title in [
        (axes[0], t_f1, t_ic, "Travel"),
        (axes[1], h_f1, h_ic, "Healthcare"),
    ]:
        bars_f1 = ax.bar(x - width / 2, f1_vals, width,
                         label="Micro-F1", color=COLORS["bar_f1"],
                         edgecolor="white", linewidth=0.5)
        bars_ic = ax.bar(x + width / 2, ic_vals, width,
                         label="Micro-IC", color=COLORS["bar_ic"],
                         edgecolor="white", linewidth=0.5)

        # Value labels on top of bars
        for bar in bars_f1:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.012,
                    f"{bar.get_height():.3f}",
                    ha="center", va="bottom", fontsize=7.5)
        for bar in bars_ic:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.012,
                    f"{bar.get_height():.3f}",
                    ha="center", va="bottom", fontsize=7.5)

        ax.set_title(title, fontweight="bold", pad=6)
        ax.set_xticks(x)
        ax.set_xticklabels(method_labels)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("Score") if ax is axes[0] else None
        ax.yaxis.set_tick_params(labelleft=True)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines[["top", "right"]].set_visible(False)

    legend_patches = [
        mpatches.Patch(color=COLORS["bar_f1"], label="Micro-F1"),
        mpatches.Patch(color=COLORS["bar_ic"], label="Micro-IC"),
    ]
    fig.legend(handles=legend_patches, loc="lower center",
               ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.04))

    out = OUTPUT_DIR / "fig_method_comparison.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  Written: {out}")


# ── Figure 2: Category Distribution ───────────────────────────────────────────
def make_distributions():
    """
    Horizontal stacked bar chart showing category proportions
    for Travel and Healthcare (one bar each).
    """
    travel_constraints     = load_gold("annotations_travel_gold.json")
    healthcare_constraints = load_gold("annotations_healthcare_gold.json")

    def count_cats(constraints):
        total = len(constraints)
        c = Counter(x["category"] for x in constraints)
        return [c.get(cat, 0) / total * 100 for cat in CATEGORY_ORDER]

    t_pcts = count_cats(travel_constraints)
    h_pcts = count_cats(healthcare_constraints)

    fig, ax = plt.subplots(figsize=(9, 2.6))

    y_pos    = [1.0, 0.0]
    labels   = ["Travel\n(n=88)", "Healthcare\n(n=85)"]
    all_pcts = [t_pcts, h_pcts]

    lefts = [0, 0]
    bar_height = 0.45

    for i, (cat, color) in enumerate(zip(CATEGORY_ORDER, CATEGORY_COLORS)):
        vals = [pcts[i] for pcts in all_pcts]
        bars = ax.barh(y_pos, vals, left=lefts, height=bar_height,
                       color=color, label=cat, edgecolor="white", linewidth=0.5)

        # Add percentage labels inside bars if wide enough
        for bar, left, val in zip(bars, lefts, vals):
            if val >= 8:
                ax.text(left + val / 2, bar.get_y() + bar.get_height() / 2,
                        f"{val:.1f}%", ha="center", va="center",
                        fontsize=8, color="white", fontweight="bold")

        lefts = [l + v for l, v in zip(lefts, vals)]

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Percentage of constraints (%)")
    ax.xaxis.grid(True, linestyle="--", alpha=0.4)
    ax.spines[["top", "right", "left"]].set_visible(False)

    ax.legend(handles=[mpatches.Patch(color=c, label=l)
                        for c, l in zip(CATEGORY_COLORS, CATEGORY_ORDER)],
              loc="lower center", ncol=4, frameon=False,
              bbox_to_anchor=(0.5, -0.38))

    fig.tight_layout()
    out = OUTPUT_DIR / "fig_distributions.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  Written: {out}")


# ── Figure 3: Hallucination Rate ───────────────────────────────────────────────
def make_hallucination():
    """
    Grouped bar chart: hallucination rate by method and domain.
    """
    travel_data     = load_comparison("travel")
    healthcare_data = load_comparison("healthcare")

    method_keys   = COLORS["method_keys"]
    method_labels = COLORS["methods_order"]

    def _hallucination_rate_from_metrics(metrics: dict) -> float:
        """
        Return hallucination rate in [0,1] from aggregate metric fields.
        Supports both new JSONs with `hallucination_rate` and older schemas.
        """
        if "hallucination_rate" in metrics:
            return float(metrics["hallucination_rate"])

        # Fallback for older aggregate schemas that only expose counts.
        fp = float(metrics.get("total_hallucinated", 0))
        if fp <= 0:
            return 0.0

        # Preferred denominator if present: matched + hallucinated.
        if "total_matched" in metrics:
            tp = float(metrics.get("total_matched", 0))
            denom = tp + fp
            return (fp / denom) if denom > 0 else 0.0

        # Derive matched from precision: precision = tp / (tp + fp).
        p = float(metrics.get("micro_precision", 0.0))
        if 0.0 < p < 1.0:
            tp = (p * fp) / (1.0 - p)
            denom = tp + fp
            return (fp / denom) if denom > 0 else 0.0

        # If precision is 0 or 1, rate is implied by fp and missing tp evidence.
        return 1.0 if p <= 0.0 and fp > 0 else 0.0

    def extract_hall(comp_data):
        rows = {m["method"]: m["aggregate_metrics"] for m in comp_data["methods"]}
        return [_hallucination_rate_from_metrics(rows[k]) * 100 for k in method_keys]

    t_hall = extract_hall(travel_data)
    h_hall = extract_hall(healthcare_data)

    x     = np.arange(len(method_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 4))

    bars_t = ax.bar(x - width / 2, t_hall, width,
                    label="Travel", color=COLORS["travel"],
                    edgecolor="white", linewidth=0.5)
    bars_h = ax.bar(x + width / 2, h_hall, width,
                    label="Healthcare", color=COLORS["healthcare"],
                    edgecolor="white", linewidth=0.5)

    for bars in [bars_t, bars_h]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 1.0,
                    f"{bar.get_height():.1f}%",
                    ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(method_labels)
    ax.set_ylabel("Hallucination rate (%)")
    ax.set_ylim(0, 85)
    ax.legend(frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.spines[["top", "right"]].set_visible(False)

    out = OUTPUT_DIR / "fig_hallucination.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  Written: {out}")


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating thesis figures...")
    print(f"  Output directory: {OUTPUT_DIR}\n")

    make_method_comparison()
    make_distributions()
    make_hallucination()

    print("\nDone. Three PDF figures written to RQ2/eval/results/figures/")
    print("Upload figures/ to Overleaf and replace the \\fbox placeholders in main.tex.")
