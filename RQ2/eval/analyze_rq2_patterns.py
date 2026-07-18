#!/usr/bin/env python3
"""
Consolidated RQ2 analysis.

Generates one consistent set of artifacts for:
- Category prevalence (full gold + subset)
- Category-wise extraction performance
- Resolvability-wise extraction performance
- Importance-wise extraction performance
- Density-wise request performance

By default, uses the same alignment settings used for final evaluator runs.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import evaluate_rq2 as ev


CATEGORIES = ["Temporal", "Spatial", "Logical", "Domain-default"]
RESOLVABILITY_LABELS = ["Implicit", "Vague", "Borderline"]
IMPORTANCE_LABELS = ["Critical", "Useful", "Optional"]
DENSITY_LABELS = ["Low", "Medium", "High"]
METHODS = ["zeroshot", "fewshot", "cot", "hybrid"]
DOMAINS = ["travel", "healthcare"]


@dataclass
class LabelStats:
    gold_count: int = 0
    pred_count: int = 0
    matched_count: int = 0


def safe_div(n: float, d: float) -> float:
    return n / d if d else 0.0


def f1(p: float, r: float) -> float:
    return safe_div(2 * p * r, p + r)


def label_key(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def count_categories(constraints_by_request: List[Dict[str, Any]]) -> Dict[str, int]:
    # Count label frequencies exactly as stored in the gold/subset files.
    counts = {k: 0 for k in CATEGORIES}
    for item in constraints_by_request:
        for c in item.get("constraints", []):
            cat = c.get("category")
            if cat in counts:
                counts[cat] += 1
    return counts


def first_existing(base: Path, candidates: List[str]) -> Path:
    for candidate in candidates:
        path = base / candidate
        if path.exists() and path.is_file():
            return path
    raise FileNotFoundError(f"No file found in candidates: {candidates} under {base}")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_prevalence_rows(root: Path) -> List[Dict[str, Any]]:
    data_dir = root / "data"
    rows: List[Dict[str, Any]] = []

    full_overall = {c: 0 for c in CATEGORIES}
    subset_overall = {c: 0 for c in CATEGORIES}

    for domain in DOMAINS:
        cfg = ev.get_domain_config(domain)
        gold_path = first_existing(data_dir, cfg.gold_file_candidates)
        subset_path = first_existing(data_dir, cfg.subset_file_candidates)

        gold_payload = ev.load_json_file(gold_path)
        full_annotations = gold_payload.get("annotations", [])

        gold_by_id = ev.load_gold_requests(gold_path)
        subset_ids, _warnings = ev.load_subset_ids(subset_path, False, gold_by_id)
        subset_set = set(subset_ids)
        # Keep only gold annotations that belong to the evaluation subset.
        subset_annotations = [a for a in full_annotations if a.get("request_id") in subset_set]

        full_counts = count_categories(full_annotations)
        subset_counts = count_categories(subset_annotations)

        for category in CATEGORIES:
            full_overall[category] += full_counts[category]
            subset_overall[category] += subset_counts[category]

        for scope, counts in (("full_gold", full_counts), ("subset", subset_counts)):
            total = sum(counts.values())
            row = {
                "domain": domain,
                "scope": scope,
                "total_constraints": total,
            }
            for category in CATEGORIES:
                key = category.lower().replace("-", "_")
                row[f"count_{key}"] = counts[category]
                row[f"pct_{key}"] = round(safe_div(counts[category], total) * 100.0, 2)
            rows.append(row)

    for scope, counts in (("full_gold", full_overall), ("subset", subset_overall)):
        total = sum(counts.values())
        row = {
            "domain": "overall",
            "scope": scope,
            "total_constraints": total,
        }
        for category in CATEGORIES:
            key = category.lower().replace("-", "_")
            row[f"count_{key}"] = counts[category]
            row[f"pct_{key}"] = round(safe_div(counts[category], total) * 100.0, 2)
        rows.append(row)

    return rows


def summarize_label_stats(
    domain: str,
    method: str,
    label_type: str,
    labels: List[str],
    stats: Dict[str, LabelStats],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for label in labels:
        s = stats.get(label, LabelStats())
        p = safe_div(s.matched_count, s.pred_count)
        r = safe_div(s.matched_count, s.gold_count)
        rows.append(
            {
                "domain": domain,
                "method": method,
                "label_type": label_type,
                "label": label,
                "gold_count": s.gold_count,
                "pred_count": s.pred_count,
                "matched_count": s.matched_count,
                "precision": round(p, 6),
                "recall": round(r, 6),
                "f1": round(f1(p, r), 6),
            }
        )
    return rows


def run_pattern_analysis(
    root: Path,
    match_threshold: float,
    category_bonus: float,
    hybrid_source: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    data_dir = root / "data"

    category_rows: List[Dict[str, Any]] = []
    resolvability_rows: List[Dict[str, Any]] = []
    importance_rows: List[Dict[str, Any]] = []
    density_rows: List[Dict[str, Any]] = []

    for domain in DOMAINS:
        cfg = ev.get_domain_config(domain)
        gold_path = first_existing(data_dir, cfg.gold_file_candidates)
        subset_path = first_existing(data_dir, cfg.subset_file_candidates)

        gold_by_id = ev.load_gold_requests(gold_path)
        subset_ids, _ = ev.load_subset_ids(subset_path, False, gold_by_id)

        for method in METHODS:
            method_folder, _ = ev.resolve_method_folder(root, method)
            pred_dir, _ = ev.resolve_prediction_folder(method_folder, method, cfg, hybrid_source)
            predictions_by_id, _warnings, _count = ev.load_predictions(pred_dir, debug=False)

            category_stats = {label: LabelStats() for label in CATEGORIES}
            resolvability_stats = {label: LabelStats() for label in RESOLVABILITY_LABELS}
            importance_stats = {label: LabelStats() for label in IMPORTANCE_LABELS}
            density_accumulator = {
                label: {"count": 0, "precision_sum": 0.0, "recall_sum": 0.0, "f1_sum": 0.0}
                for label in DENSITY_LABELS
            }

            for request_id in subset_ids:
                gold_item = gold_by_id.get(request_id)
                if not gold_item:
                    continue

                gold_constraints = gold_item.get("constraints", [])
                pred_payload = predictions_by_id.get(request_id)
                pred_constraints = pred_payload.payload.get("constraints", []) if pred_payload else []

                alignment = ev.align_constraints_greedy(
                    gold_constraints=gold_constraints,
                    pred_constraints=pred_constraints,
                    domain=domain,
                    match_threshold=match_threshold,
                    category_bonus=category_bonus,
                )

                tp = len(alignment.matches)
                fp = len(alignment.unmatched_pred)
                fn = len(alignment.unmatched_gold)
                precision = safe_div(tp, tp + fp)
                recall = safe_div(tp, tp + fn)
                req_f1 = f1(precision, recall)

                density = label_key(gold_item.get("density"))
                if density in density_accumulator:
                    # Average request-level scores per density bucket.
                    density_accumulator[density]["count"] += 1
                    density_accumulator[density]["precision_sum"] += precision
                    density_accumulator[density]["recall_sum"] += recall
                    density_accumulator[density]["f1_sum"] += req_f1

                for gc in gold_constraints:
                    cat = label_key(gc.get("category"))
                    res = label_key(gc.get("resolvability"))
                    imp = label_key(gc.get("importance"))
                    if cat in category_stats:
                        category_stats[cat].gold_count += 1
                    if res in resolvability_stats:
                        resolvability_stats[res].gold_count += 1
                    if imp in importance_stats:
                        importance_stats[imp].gold_count += 1

                for pc in pred_constraints:
                    cat = label_key(pc.get("category"))
                    res = label_key(pc.get("resolvability"))
                    imp = label_key(pc.get("importance"))
                    if cat in category_stats:
                        category_stats[cat].pred_count += 1
                    if res in resolvability_stats:
                        resolvability_stats[res].pred_count += 1
                    if imp in importance_stats:
                        importance_stats[imp].pred_count += 1

                for pair in alignment.matches:
                    # A label counts as matched only when gold label equals predicted label.
                    g = gold_constraints[pair.gold_index]
                    p = pred_constraints[pair.pred_index]
                    cat = label_key(g.get("category"))
                    pred_cat = label_key(p.get("category"))
                    res = label_key(g.get("resolvability"))
                    pred_res = label_key(p.get("resolvability"))
                    imp = label_key(g.get("importance"))
                    pred_imp = label_key(p.get("importance"))
                    if cat in category_stats and cat == pred_cat:
                        category_stats[cat].matched_count += 1
                    if res in resolvability_stats and res == pred_res:
                        resolvability_stats[res].matched_count += 1
                    if imp in importance_stats and imp == pred_imp:
                        importance_stats[imp].matched_count += 1

            category_rows.extend(
                summarize_label_stats(domain, method, "category", CATEGORIES, category_stats)
            )
            resolvability_rows.extend(
                summarize_label_stats(
                    domain,
                    method,
                    "resolvability",
                    RESOLVABILITY_LABELS,
                    resolvability_stats,
                )
            )
            importance_rows.extend(
                summarize_label_stats(
                    domain,
                    method,
                    "importance",
                    IMPORTANCE_LABELS,
                    importance_stats,
                )
            )

            for density in DENSITY_LABELS:
                d = density_accumulator[density]
                count = d["count"]
                density_rows.append(
                    {
                        "domain": domain,
                        "method": method,
                        "density": density,
                        "request_count": count,
                        "avg_precision": round(safe_div(d["precision_sum"], count), 6),
                        "avg_recall": round(safe_div(d["recall_sum"], count), 6),
                        "avg_f1": round(safe_div(d["f1_sum"], count), 6),
                    }
                )

    return category_rows, resolvability_rows, importance_rows, density_rows


def write_markdown_summary(
    path: Path,
    prevalence_rows: List[Dict[str, Any]],
    category_rows: List[Dict[str, Any]],
    resolvability_rows: List[Dict[str, Any]],
    importance_rows: List[Dict[str, Any]],
    density_rows: List[Dict[str, Any]],
    travel_comparison: Dict[str, Any],
    healthcare_comparison: Dict[str, Any],
) -> None:
    lines: List[str] = []
    lines.append("# RQ2 Pattern Analysis Summary")
    lines.append("")

    lines.append("## Category Prevalence (Subset Overall)")
    subset_overall = [r for r in prevalence_rows if r["domain"] == "overall" and r["scope"] == "subset"]
    if subset_overall:
        row = subset_overall[0]
        lines.append(
            "- Temporal: "
            f"{row['count_temporal']} ({row['pct_temporal']}%), "
            f"Spatial: {row['count_spatial']} ({row['pct_spatial']}%), "
            f"Logical: {row['count_logical']} ({row['pct_logical']}%), "
            f"Domain-default: {row['count_domain_default']} ({row['pct_domain_default']}%)"
        )
    lines.append("")

    def append_label_section(
        title: str,
        rows: List[Dict[str, Any]],
        expected_labels: List[str],
    ) -> None:
        lines.append(f"#### {title}")
        valid_rows = [r for r in rows if r["gold_count"] > 0]
        if not valid_rows:
            lines.append("No gold support for this label group in the evaluated subset.")
            lines.append("")
            return

        for label in expected_labels:
            row = next((r for r in rows if r["label"] == label), None)
            if not row:
                continue
            missed = max(0, int(row["gold_count"]) - int(row["matched_count"]))
            over_pred = max(0, int(row["pred_count"]) - int(row["matched_count"]))
            lines.append(
                f"- {label}: gold={row['gold_count']}, matched={row['matched_count']}, pred={row['pred_count']}, "
                f"missed={missed}, over_pred={over_pred}, precision={row['precision']:.3f}, "
                f"recall={row['recall']:.3f}, f1={row['f1']:.3f}"
            )

        hardest = min(valid_rows, key=lambda r: (r["recall"], r["matched_count"]))
        easiest = max(valid_rows, key=lambda r: (r["recall"], r["matched_count"]))
        # These two lines make it easy to discuss weak and strong labels in the report.
        lines.append(
            f"Most difficult label (lowest recall): {hardest['label']} "
            f"(recall={hardest['recall']:.3f}, matched={hardest['matched_count']}/{hardest['gold_count']})"
        )
        lines.append(
            f"Best extracted label (highest recall): {easiest['label']} "
            f"(recall={easiest['recall']:.3f}, matched={easiest['matched_count']}/{easiest['gold_count']})"
        )
        lines.append("")

    lines.append("## Per-Method Extraction Difficulty (Per Domain)")
    for domain in DOMAINS:
        lines.append(f"### Domain: {domain}")
        lines.append("")
        for method in METHODS:
            lines.append(f"#### Method: {method}")

            category_slice = [
                r for r in category_rows if r["domain"] == domain and r["method"] == method
            ]
            append_label_section("Category-level extraction", category_slice, CATEGORIES)

            resolvability_slice = [
                r for r in resolvability_rows if r["domain"] == domain and r["method"] == method
            ]
            append_label_section(
                "Resolvability-level extraction",
                resolvability_slice,
                RESOLVABILITY_LABELS,
            )

            importance_slice = [
                r for r in importance_rows if r["domain"] == domain and r["method"] == method
            ]
            append_label_section(
                "Importance-level extraction",
                importance_slice,
                IMPORTANCE_LABELS,
            )

            density_slice = [
                r for r in density_rows if r["domain"] == domain and r["method"] == method
            ]
            density_slice = sorted(density_slice, key=lambda x: DENSITY_LABELS.index(x["density"]))
            if density_slice:
                density_text = ", ".join(
                    f"{r['density']} F1={r['avg_f1']:.3f} (n={r['request_count']})"
                    for r in density_slice
                )
                lines.append(f"#### Density trend: {density_text}")
                lines.append("")

    lines.extend(generate_synthesis_table(travel_comparison, healthcare_comparison))

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_synthesis_table(travel_data: Dict[str, Any], hc_data: Dict[str, Any]) -> List[str]:
    """Build cross-domain synthesis table from comparison JSON payloads."""
    travel_methods = {
        item.get("method", ""): item.get("aggregate_metrics", {})
        for item in travel_data.get("methods", [])
        if isinstance(item, dict)
    }
    hc_methods = {
        item.get("method", ""): item.get("aggregate_metrics", {})
        for item in hc_data.get("methods", [])
        if isinstance(item, dict)
    }

    rows: List[Dict[str, Any]] = []
    for method in METHODS:
        travel_agg = travel_methods.get(method, {})
        hc_agg = hc_methods.get(method, {})

        travel_micro_f1 = float(travel_agg.get("micro_f1", 0.0) or 0.0)
        healthcare_micro_f1 = float(hc_agg.get("micro_f1", 0.0) or 0.0)
        travel_micro_ic = float(travel_agg.get("micro_intent_completeness", 0.0) or 0.0)
        healthcare_micro_ic = float(hc_agg.get("micro_intent_completeness", 0.0) or 0.0)

        rows.append(
            {
                "method": method,
                "travel_micro_f1": travel_micro_f1,
                "healthcare_micro_f1": healthcare_micro_f1,
                "travel_micro_ic": travel_micro_ic,
                "healthcare_micro_ic": healthcare_micro_ic,
                "avg_f1": (travel_micro_f1 + healthcare_micro_f1) / 2.0,
                "avg_ic": (travel_micro_ic + healthcare_micro_ic) / 2.0,
            }
        )

    rows.sort(key=lambda row: row["avg_f1"], reverse=True)

    travel_f1_values = [float(item.get("aggregate_metrics", {}).get("micro_f1", 0.0) or 0.0) for item in travel_data.get("methods", [])]
    healthcare_f1_values = [float(item.get("aggregate_metrics", {}).get("micro_f1", 0.0) or 0.0) for item in hc_data.get("methods", [])]

    travel_range = (max(travel_f1_values) - min(travel_f1_values)) if len(travel_f1_values) > 1 else 0.0
    healthcare_range = (max(healthcare_f1_values) - min(healthcare_f1_values)) if len(healthcare_f1_values) > 1 else 0.0

    best_avg_f1 = max(rows, key=lambda row: row["avg_f1"]) if rows else None
    best_avg_ic = max(rows, key=lambda row: row["avg_ic"]) if rows else None

    lines: List[str] = []
    lines.append("## Cross-Domain Synthesis")
    lines.append("")
    lines.append("| Method | T-F1 | H-F1 | T-IC | H-IC | Avg-F1 | Avg-IC |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['method']} | {row['travel_micro_f1']:.3f} | {row['healthcare_micro_f1']:.3f} | "
            f"{row['travel_micro_ic']:.3f} | {row['healthcare_micro_ic']:.3f} | "
            f"{row['avg_f1']:.3f} | {row['avg_ic']:.3f} |"
        )

    if best_avg_f1 and best_avg_ic:
        lines.append("")
        lines.append(
            "Best Avg-F1 method: "
            f"{best_avg_f1['method']} ({best_avg_f1['avg_f1']:.3f}) | "
            "Best Avg-IC method: "
            f"{best_avg_ic['method']} ({best_avg_ic['avg_ic']:.3f})"
        )

    lines.append(
        f"Travel F1 range: {travel_range:.3f} | Healthcare F1 range: {healthcare_range:.3f}"
    )
    lines.append("")
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consolidated RQ2 pattern analysis")
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Optional RQ2 root directory. Defaults to eval script parent.",
    )
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.25,
        help="Matching threshold (should match evaluator run config).",
    )
    parser.add_argument(
        "--category-bonus",
        type=float,
        default=0.05,
        help="Category bonus (should match evaluator run config).",
    )
    parser.add_argument(
        "--hybrid-source",
        choices=["validator", "llm"],
        default="validator",
        help="Hybrid prediction source priority.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.base_dir:
        rq2_root = Path(args.base_dir).expanduser().resolve()
    else:
        rq2_root = Path(__file__).resolve().parents[1]

    output_dir = rq2_root / "eval" / "results" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    comparison_dir = rq2_root / "eval" / "results" / "comparisons"

    travel_comparison_path = comparison_dir / "travel_method_comparison.json"
    healthcare_comparison_path = comparison_dir / "healthcare_method_comparison.json"
    travel_comparison_data = json.loads(travel_comparison_path.read_text(encoding="utf-8"))
    healthcare_comparison_data = json.loads(healthcare_comparison_path.read_text(encoding="utf-8"))

    prevalence_rows = build_prevalence_rows(rq2_root)
    category_rows, resolvability_rows, importance_rows, density_rows = run_pattern_analysis(
        rq2_root,
        match_threshold=args.match_threshold,
        category_bonus=args.category_bonus,
        hybrid_source=args.hybrid_source,
    )

    write_csv(
        output_dir / "category_prevalence.csv",
        prevalence_rows,
        [
            "domain",
            "scope",
            "total_constraints",
            "count_temporal",
            "pct_temporal",
            "count_spatial",
            "pct_spatial",
            "count_logical",
            "pct_logical",
            "count_domain_default",
            "pct_domain_default",
        ],
    )
    write_csv(
        output_dir / "category_performance.csv",
        category_rows,
        [
            "domain",
            "method",
            "label_type",
            "label",
            "gold_count",
            "pred_count",
            "matched_count",
            "precision",
            "recall",
            "f1",
        ],
    )
    write_csv(
        output_dir / "resolvability_performance.csv",
        resolvability_rows,
        [
            "domain",
            "method",
            "label_type",
            "label",
            "gold_count",
            "pred_count",
            "matched_count",
            "precision",
            "recall",
            "f1",
        ],
    )
    write_csv(
        output_dir / "importance_performance.csv",
        importance_rows,
        [
            "domain",
            "method",
            "label_type",
            "label",
            "gold_count",
            "pred_count",
            "matched_count",
            "precision",
            "recall",
            "f1",
        ],
    )
    write_csv(
        output_dir / "density_performance.csv",
        density_rows,
        ["domain", "method", "density", "request_count", "avg_precision", "avg_recall", "avg_f1"],
    )

    consolidated = {
        "config": {
            "match_threshold": args.match_threshold,
            "category_bonus": args.category_bonus,
            "hybrid_source": args.hybrid_source,
        },
        "prevalence": prevalence_rows,
        "category_performance": category_rows,
        "resolvability_performance": resolvability_rows,
        "importance_performance": importance_rows,
        "density_performance": density_rows,
    }
    (output_dir / "rq2_pattern_analysis.json").write_text(
        json.dumps(consolidated, indent=2), encoding="utf-8"
    )

    write_markdown_summary(
        output_dir / "rq2_pattern_analysis.md",
        prevalence_rows,
        category_rows,
        resolvability_rows,
        importance_rows,
        density_rows,
        travel_comparison_data,
        healthcare_comparison_data,
    )

    print("Wrote consolidated analysis artifacts:")
    print(f"- {output_dir / 'category_prevalence.csv'}")
    print(f"- {output_dir / 'category_performance.csv'}")
    print(f"- {output_dir / 'resolvability_performance.csv'}")
    print(f"- {output_dir / 'importance_performance.csv'}")
    print(f"- {output_dir / 'density_performance.csv'}")
    print(f"- {output_dir / 'rq2_pattern_analysis.json'}")
    print(f"- {output_dir / 'rq2_pattern_analysis.md'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
