#!/usr/bin/env python3
"""
RQ2 evaluator (Phase 1-5 implementation).

Currently implemented:
- CLI parsing
- path and config resolution
- loading gold/subset/prediction JSON files
- strict schema validation for prediction JSON files
- deterministic normalization + alignment
- per-request and aggregate metrics in console output
- CSV/JSON/Markdown reporting artifacts
- acceptance checks and non-zero exit codes for validation policy

Not implemented here:
- any prompt-generation or annotation-inference logic (out of scope)
"""

from __future__ import annotations

import argparse
import csv
import difflib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Canonical method names we will use everywhere in the evaluator.
CANONICAL_METHODS = ["zeroshot", "fewshot", "cot", "hybrid"]

# Allowed aliases keep CLI user-friendly while preserving canonical names internally.
METHOD_ALIASES = {
    "zeroshot": "zeroshot",
    "zero-shot": "zeroshot",
    "zero_shot": "zeroshot",
    "zero shot": "zeroshot",
    "fewshot": "fewshot",
    "few-shot": "fewshot",
    "few_shot": "fewshot",
    "few shot": "fewshot",
    "cot": "cot",
    "chain-of-thought": "cot",
    "chain_of_thought": "cot",
    "tot": "cot",
    "tree-of-thought": "cot",
    "tree_of_thought": "cot",
    "hybrid": "hybrid",
}

# Domain aliases map to two canonical domains used in this script.
DOMAIN_ALIASES = {
    "travel": "travel",
    "travel_booking": "travel",
    "healthcare": "healthcare",
    "health": "healthcare",
    "healthcare_booking": "healthcare",
}


@dataclass
class DomainConfig:
    canonical_name: str
    gold_file_candidates: List[str]
    subset_file_candidates: List[str]
    prediction_subdir: str


@dataclass
class LoadedPrediction:
    request_id: str
    source_file: Path
    payload: Dict[str, Any]


@dataclass
class MatchedPair:
    gold_index: int
    pred_index: int
    score: float
    base_similarity: float
    category_bonus_applied: float


@dataclass
class AlignmentResult:
    matches: List[MatchedPair]
    unmatched_gold: List[int]
    unmatched_pred: List[int]


@dataclass
class RequestMetrics:
    request_id: str
    gold_count: int
    pred_count: int
    matched_count: int
    weighted_matched: float
    weighted_total: float
    precision: float
    recall: float
    f1: float
    intent_completeness: float
    category_accuracy: float
    resolvability_accuracy: float
    importance_accuracy: float
    missing_count: int
    hallucinated_count: int
    misclassified_count: int
    vague_non_resolvable_count: int
    critical_matched_count: int
    critical_total_count: int


@dataclass
class AggregateMetrics:
    requests_evaluated: int
    micro_precision: float
    micro_recall: float
    micro_f1: float
    micro_intent_completeness: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    macro_intent_completeness: float
    micro_category_accuracy: float
    micro_resolvability_accuracy: float
    micro_importance_accuracy: float
    macro_category_accuracy: float
    macro_resolvability_accuracy: float
    macro_importance_accuracy: float
    total_missing: int
    total_hallucinated: int
    total_misclassified: int
    total_vague_non_resolvable: int
    hallucination_rate: float
    critical_recall: float
    total_critical_matched: int
    total_critical_total: int
    performance_range: float


@dataclass
class RunResult:
    domain: str
    method: str
    gold_path: Path
    subset_path: Path
    prediction_path: Path
    subset_count: int
    gold_count: int
    prediction_file_count: int
    total_alignment_matches: int
    request_metrics: List[RequestMetrics]
    aggregate_metrics: AggregateMetrics
    missing_prediction_ids: List[str]
    extra_prediction_ids: List[str]
    warnings: List[str]


@dataclass
class RunConfig:
    match_threshold: float
    category_bonus: float
    hybrid_source: str
    allow_subset_fallback: bool
    warnings_as_errors: bool
    require_complete_predictions: bool


@dataclass
class AcceptanceSummary:
    total_warnings: int
    total_missing_predictions: int
    total_extra_predictions: int


class ExitCode(IntEnum):
    SUCCESS = 0
    CONFIG_ERROR = 2
    DATA_ERROR = 3
    VALIDATION_ERROR = 4
    ACCEPTANCE_FAILED = 5
    UNEXPECTED_ERROR = 10


class EvaluationError(Exception):
    """Structured evaluator exception with stable exit code."""

    def __init__(self, message: str, exit_code: ExitCode) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def build_cli_parser() -> argparse.ArgumentParser:
    """Build CLI for evaluator execution and artifact generation."""
    parser = argparse.ArgumentParser(
        description="RQ2 evaluator: load data, align constraints, compute metrics, and write artifacts."
    )
    parser.add_argument(
        "--domain",
        required=True,
        choices=["travel", "healthcare", "all"],
        help="Domain to inspect.",
    )
    parser.add_argument(
        "--method",
        required=True,
        choices=["zeroshot", "fewshot", "cot", "hybrid", "all"],
        help="Method to inspect.",
    )
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Optional override for RQ2 project directory. If omitted, inferred from this script location.",
    )
    parser.add_argument(
        "--hybrid-source",
        choices=["validator", "llm"],
        default="validator",
        help="Preferred source when method is hybrid.",
    )
    parser.add_argument(
        "--allow-subset-fallback",
        action="store_true",
        help=(
            "If subset file is missing, allow fallback to gold request IDs. "
            "By default this is disabled to avoid silent fallback."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print extra debug details while loading files.",
    )
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.25,
        help="Phase 2: minimum score to consider a gold-prediction pair as a valid match.",
    )
    parser.add_argument(
        "--category-bonus",
        type=float,
        default=0.05,
        help="Phase 2: small soft bonus added when category labels match.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Phase 4: folder where evaluation artifacts are written. "
            "Default is RQ2/eval/results."
        ),
    )
    parser.add_argument(
        "--warnings-as-errors",
        action="store_true",
        help="Phase 5: fail the run with non-zero exit code if warnings are produced.",
    )
    parser.add_argument(
        "--require-complete-predictions",
        action="store_true",
        help=(
            "Phase 5: fail the run if any subset request_id is missing a prediction file."
        ),
    )
    return parser


def validate_phase2_args(match_threshold: float, category_bonus: float) -> None:
    """Simple guardrails for Phase 2 alignment configuration."""
    if not (0.0 <= match_threshold <= 1.0):
        raise EvaluationError(
            f"--match-threshold must be between 0 and 1, got: {match_threshold}",
            ExitCode.CONFIG_ERROR,
        )
    if not (0.0 <= category_bonus <= 1.0):
        raise EvaluationError(
            f"--category-bonus must be between 0 and 1, got: {category_bonus}",
            ExitCode.CONFIG_ERROR,
        )


def validate_run_config(run_config: RunConfig) -> None:
    """Phase 5 config checks kept explicit and easy to defend."""
    if run_config.hybrid_source not in {"validator", "llm"}:
        raise EvaluationError(
            f"Unsupported hybrid source: {run_config.hybrid_source}",
            ExitCode.CONFIG_ERROR,
        )


def safe_divide(numerator: float, denominator: float) -> float:
    """Avoid division crashes and keep metric behavior explicit."""
    # Returning 0.0 here keeps metric math stable when a denominator is empty.
    if denominator == 0:
        return 0.0
    return numerator / denominator


def importance_weight(importance_value: Any) -> float:
    """Weights for intent completeness as defined in rq2_methodology."""
    # Critical constraints should matter most in intent completeness.
    label = normalize_label(importance_value)
    if label == "critical":
        return 1.0
    if label == "useful":
        return 0.5
    if label == "optional":
        return 0.2
    return 0.0


def is_vague_or_non_resolvable(constraint: Dict[str, Any], domain: str) -> bool:
    """
    Phase 3 vague/non-resolvable detector.

    Rule:
    - True when resolvability label is Vague or Borderline.
    - Also true when description contains transparent heuristic vague terms.
    """
    resolvability = normalize_label(constraint.get("resolvability", ""))
    if resolvability in {"vague", "borderline"}:
        return True

    description = normalize_constraint_text(constraint.get("description", ""), domain)
    if not description:
        return False

    # This is an intentionally simple heuristic list for transparency.
    vague_terms = {
        "soon",
        "good",
        "nice",
        "cheap",
        "affordable",
        "near",
        "close",
        "reasonable",
        "comfortable",
        "early",
        "late",
        "preferably",
        "flexible",
        "asap",
        "quick",
    }
    tokens = set(tokenize_normalized_text(description))
    return len(tokens & vague_terms) > 0


def compute_request_metrics(
    request_id: str,
    domain: str,
    gold_constraints: List[Dict[str, Any]],
    pred_constraints: List[Dict[str, Any]],
    alignment_result: AlignmentResult,
) -> RequestMetrics:
    """Compute Phase 3 metrics for one request."""
    # Start from plain TP/FP/FN based on alignment output.
    gold_count = len(gold_constraints)
    pred_count = len(pred_constraints)
    matched_count = len(alignment_result.matches)

    tp = matched_count
    fp = len(alignment_result.unmatched_pred)
    fn = len(alignment_result.unmatched_gold)

    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    f1 = safe_divide(2 * precision * recall, precision + recall)

    matched_gold_indices = {pair.gold_index for pair in alignment_result.matches}
    # Intent completeness uses weighted gold coverage, not raw match count only.
    weighted_total = sum(importance_weight(item.get("importance", "")) for item in gold_constraints)
    weighted_matched = sum(
        importance_weight(gold_constraints[idx].get("importance", ""))
        for idx in matched_gold_indices
    )
    intent_completeness = safe_divide(weighted_matched, weighted_total)

    category_correct = 0
    resolvability_correct = 0
    importance_correct = 0
    misclassified_count = 0

    for pair in alignment_result.matches:
        gold_item = gold_constraints[pair.gold_index]
        pred_item = pred_constraints[pair.pred_index]

        category_match = normalize_label(gold_item.get("category", "")) == normalize_label(
            pred_item.get("category", "")
        )
        resolvability_match = normalize_label(gold_item.get("resolvability", "")) == normalize_label(
            pred_item.get("resolvability", "")
        )
        importance_match = normalize_label(gold_item.get("importance", "")) == normalize_label(
            pred_item.get("importance", "")
        )

        if category_match:
            category_correct += 1
        if resolvability_match:
            resolvability_correct += 1
        if importance_match:
            importance_correct += 1

        if not (category_match and resolvability_match and importance_match):
            misclassified_count += 1

    category_accuracy = safe_divide(category_correct, matched_count)
    resolvability_accuracy = safe_divide(resolvability_correct, matched_count)
    importance_accuracy = safe_divide(importance_correct, matched_count)

    vague_non_resolvable_count = sum(
        1 for item in pred_constraints if is_vague_or_non_resolvable(item, domain)
    )

    critical_total_count = sum(
        1 for item in gold_constraints
        if normalize_label(item.get("importance", "")) == "critical"
    )
    critical_matched_count = sum(
        1 for pair in alignment_result.matches
        if normalize_label(
            gold_constraints[pair.gold_index].get("importance", "")
        ) == "critical"
    )

    return RequestMetrics(
        request_id=request_id,
        gold_count=gold_count,
        pred_count=pred_count,
        matched_count=matched_count,
        weighted_matched=weighted_matched,
        weighted_total=weighted_total,
        precision=precision,
        recall=recall,
        f1=f1,
        intent_completeness=intent_completeness,
        category_accuracy=category_accuracy,
        resolvability_accuracy=resolvability_accuracy,
        importance_accuracy=importance_accuracy,
        missing_count=fn,
        hallucinated_count=fp,
        misclassified_count=misclassified_count,
        vague_non_resolvable_count=vague_non_resolvable_count,
        critical_matched_count=critical_matched_count,
        critical_total_count=critical_total_count,
    )


def aggregate_request_metrics(request_metrics: List[RequestMetrics]) -> AggregateMetrics:
    """Build micro and macro summaries from request-level metrics."""
    # Micro = global pooled counts. Macro = average of request-level scores.
    requests_evaluated = len(request_metrics)

    total_tp = sum(item.matched_count for item in request_metrics)
    total_fp = sum(item.hallucinated_count for item in request_metrics)
    total_fn = sum(item.missing_count for item in request_metrics)

    micro_precision = safe_divide(total_tp, total_tp + total_fp)
    micro_recall = safe_divide(total_tp, total_tp + total_fn)
    micro_f1 = safe_divide(2 * micro_precision * micro_recall, micro_precision + micro_recall)

    micro_weighted_matched = sum(item.weighted_matched for item in request_metrics)
    micro_weighted_total = sum(item.weighted_total for item in request_metrics)
    micro_intent_completeness = safe_divide(micro_weighted_matched, micro_weighted_total)

    macro_precision = safe_divide(sum(item.precision for item in request_metrics), requests_evaluated)
    macro_recall = safe_divide(sum(item.recall for item in request_metrics), requests_evaluated)
    macro_f1 = safe_divide(sum(item.f1 for item in request_metrics), requests_evaluated)
    macro_intent_completeness = safe_divide(
        sum(item.intent_completeness for item in request_metrics), requests_evaluated
    )

    matched_total = sum(item.matched_count for item in request_metrics)
    # Accuracy-by-label is computed over matched pairs only.
    micro_category_correct = sum(item.category_accuracy * item.matched_count for item in request_metrics)
    micro_resolvability_correct = sum(
        item.resolvability_accuracy * item.matched_count for item in request_metrics
    )
    micro_importance_correct = sum(item.importance_accuracy * item.matched_count for item in request_metrics)

    micro_category_accuracy = safe_divide(micro_category_correct, matched_total)
    micro_resolvability_accuracy = safe_divide(micro_resolvability_correct, matched_total)
    micro_importance_accuracy = safe_divide(micro_importance_correct, matched_total)

    macro_category_accuracy = safe_divide(
        sum(item.category_accuracy for item in request_metrics), requests_evaluated
    )
    macro_resolvability_accuracy = safe_divide(
        sum(item.resolvability_accuracy for item in request_metrics), requests_evaluated
    )
    macro_importance_accuracy = safe_divide(
        sum(item.importance_accuracy for item in request_metrics), requests_evaluated
    )

    total_missing = sum(item.missing_count for item in request_metrics)
    total_hallucinated = sum(item.hallucinated_count for item in request_metrics)
    total_misclassified = sum(item.misclassified_count for item in request_metrics)
    total_vague_non_resolvable = sum(item.vague_non_resolvable_count for item in request_metrics)

    total_critical_matched = sum(item.critical_matched_count for item in request_metrics)
    total_critical_total = sum(item.critical_total_count for item in request_metrics)
    critical_recall = (
        total_critical_matched / total_critical_total
        if total_critical_total > 0 else 0.0
    )

    total_matched_agg = sum(item.matched_count for item in request_metrics)
    total_hallucinated_agg = sum(item.hallucinated_count for item in request_metrics)
    hallucination_rate = (
        total_hallucinated_agg / (total_matched_agg + total_hallucinated_agg)
        if (total_matched_agg + total_hallucinated_agg) > 0 else 0.0
    )

    performance_range = 0.0  # placeholder, filled at comparison level

    return AggregateMetrics(
        requests_evaluated=requests_evaluated,
        micro_precision=micro_precision,
        micro_recall=micro_recall,
        micro_f1=micro_f1,
        micro_intent_completeness=micro_intent_completeness,
        macro_precision=macro_precision,
        macro_recall=macro_recall,
        macro_f1=macro_f1,
        macro_intent_completeness=macro_intent_completeness,
        micro_category_accuracy=micro_category_accuracy,
        micro_resolvability_accuracy=micro_resolvability_accuracy,
        micro_importance_accuracy=micro_importance_accuracy,
        macro_category_accuracy=macro_category_accuracy,
        macro_resolvability_accuracy=macro_resolvability_accuracy,
        macro_importance_accuracy=macro_importance_accuracy,
        total_missing=total_missing,
        total_hallucinated=total_hallucinated,
        total_misclassified=total_misclassified,
        total_vague_non_resolvable=total_vague_non_resolvable,
        hallucination_rate=hallucination_rate,
        critical_recall=critical_recall,
        total_critical_matched=total_critical_matched,
        total_critical_total=total_critical_total,
        performance_range=performance_range,
    )


def resolve_output_root(root: Path, output_dir_arg: Optional[str]) -> Path:
    """Resolve the base folder for Phase 4 output artifacts."""
    if output_dir_arg:
        output_root = Path(output_dir_arg).expanduser().resolve()
    else:
        output_root = root / "eval" / "results"
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def request_metrics_to_dict(item: RequestMetrics) -> Dict[str, Any]:
    """Convert request metric dataclass to JSON-friendly dict."""
    return {
        "request_id": item.request_id,
        "gold_count": item.gold_count,
        "pred_count": item.pred_count,
        "matched_count": item.matched_count,
        "precision": item.precision,
        "recall": item.recall,
        "f1": item.f1,
        "intent_completeness": item.intent_completeness,
        "category_accuracy": item.category_accuracy,
        "resolvability_accuracy": item.resolvability_accuracy,
        "importance_accuracy": item.importance_accuracy,
        "missing_count": item.missing_count,
        "hallucinated_count": item.hallucinated_count,
        "misclassified_count": item.misclassified_count,
        "vague_non_resolvable_count": item.vague_non_resolvable_count,
        "critical_matched_count": item.critical_matched_count,
        "critical_total_count": item.critical_total_count,
    }


def aggregate_metrics_to_dict(item: AggregateMetrics) -> Dict[str, Any]:
    """Convert aggregate metric dataclass to JSON-friendly dict."""
    return {
        "requests_evaluated": item.requests_evaluated,
        "micro_precision": item.micro_precision,
        "micro_recall": item.micro_recall,
        "micro_f1": item.micro_f1,
        "micro_intent_completeness": item.micro_intent_completeness,
        "macro_precision": item.macro_precision,
        "macro_recall": item.macro_recall,
        "macro_f1": item.macro_f1,
        "macro_intent_completeness": item.macro_intent_completeness,
        "micro_category_accuracy": item.micro_category_accuracy,
        "micro_resolvability_accuracy": item.micro_resolvability_accuracy,
        "micro_importance_accuracy": item.micro_importance_accuracy,
        "macro_category_accuracy": item.macro_category_accuracy,
        "macro_resolvability_accuracy": item.macro_resolvability_accuracy,
        "macro_importance_accuracy": item.macro_importance_accuracy,
        "total_missing": item.total_missing,
        "total_hallucinated": item.total_hallucinated,
        "total_misclassified": item.total_misclassified,
        "total_vague_non_resolvable": item.total_vague_non_resolvable,
        "hallucination_rate": round(item.hallucination_rate, 3),
        "critical_recall": round(item.critical_recall, 3),
        "total_critical_matched": item.total_critical_matched,
        "total_critical_total": item.total_critical_total,
        "performance_range": round(item.performance_range, 3),
    }


def write_per_request_csv(csv_path: Path, request_metrics: List[RequestMetrics]) -> None:
    """Write per-request rows for spreadsheet/statistical analysis."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "request_id",
        "gold_count",
        "pred_count",
        "matched_count",
        "precision",
        "recall",
        "f1",
        "intent_completeness",
        "category_accuracy",
        "resolvability_accuracy",
        "importance_accuracy",
        "missing_count",
        "hallucinated_count",
        "misclassified_count",
        "vague_non_resolvable_count",
        "critical_matched_count",
        "critical_total_count",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in request_metrics:
            writer.writerow(request_metrics_to_dict(item))


def build_run_summary_json(run: RunResult, generated_at: str, run_config: RunConfig) -> Dict[str, Any]:
    """Build JSON payload for one domain-method run."""
    return {
        "generated_at": generated_at,
        "domain": run.domain,
        "method": run.method,
        "run_config": {
            "match_threshold": run_config.match_threshold,
            "category_bonus": run_config.category_bonus,
            "hybrid_source": run_config.hybrid_source,
            "allow_subset_fallback": run_config.allow_subset_fallback,
            "warnings_as_errors": run_config.warnings_as_errors,
            "require_complete_predictions": run_config.require_complete_predictions,
        },
        "paths": {
            "gold_file": str(run.gold_path),
            "subset_file": str(run.subset_path),
            "prediction_folder": str(run.prediction_path),
        },
        "counts": {
            "subset_requests": run.subset_count,
            "gold_requests": run.gold_count,
            "prediction_files": run.prediction_file_count,
            "aligned_pairs": run.total_alignment_matches,
        },
        "missing_prediction_ids": run.missing_prediction_ids,
        "extra_prediction_ids": run.extra_prediction_ids,
        "warnings": run.warnings,
        "aggregate_metrics": aggregate_metrics_to_dict(run.aggregate_metrics),
        "per_request_metrics": [request_metrics_to_dict(item) for item in run.request_metrics],
    }


def write_json_summary(json_path: Path, run: RunResult, generated_at: str, run_config: RunConfig) -> None:
    """Write machine-readable summary for reproducibility and downstream scripts."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_run_summary_json(run, generated_at, run_config)
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown_summary(md_path: Path, run: RunResult, generated_at: str, run_config: RunConfig) -> None:
    """Write a human-readable markdown summary for thesis reporting."""
    md_path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append(f"# RQ2 Evaluation Summary: {run.domain} / {run.method}")
    lines.append("")
    lines.append(f"Generated at: {generated_at}")
    lines.append("")
    lines.append("## Evaluator Configuration")
    lines.append(f"- match_threshold: {run_config.match_threshold}")
    lines.append(f"- category_bonus: {run_config.category_bonus}")
    lines.append(f"- hybrid_source: {run_config.hybrid_source}")
    lines.append(f"- allow_subset_fallback: {run_config.allow_subset_fallback}")
    lines.append(f"- warnings_as_errors: {run_config.warnings_as_errors}")
    lines.append(f"- require_complete_predictions: {run_config.require_complete_predictions}")
    lines.append("")
    lines.append("## Folder Conventions")
    lines.append("- Canonical methods: zeroshot, fewshot, cot, hybrid")
    lines.append("- Default prediction path pattern: <method>/llm_outputs/<domain>")
    lines.append("- Hybrid preferred path: hybrid/validator_outputs/<domain> (fallback to llm_outputs)")
    lines.append("")
    lines.append("## Data And Paths")
    lines.append(f"- Gold file: {run.gold_path}")
    lines.append(f"- Subset file: {run.subset_path}")
    lines.append(f"- Prediction folder: {run.prediction_path}")
    lines.append("")
    lines.append("## Run Counts")
    lines.append(f"- Subset requests loaded: {run.subset_count}")
    lines.append(f"- Gold requests loaded: {run.gold_count}")
    lines.append(f"- Prediction files found: {run.prediction_file_count}")
    lines.append(f"- Total aligned pairs: {run.total_alignment_matches}")
    lines.append("")
    lines.append("## Aggregate Metrics")
    lines.append(
        "- Micro extraction: "
        f"precision={run.aggregate_metrics.micro_precision:.3f}, "
        f"recall={run.aggregate_metrics.micro_recall:.3f}, "
        f"f1={run.aggregate_metrics.micro_f1:.3f}"
    )
    lines.append(
        "- Macro extraction: "
        f"precision={run.aggregate_metrics.macro_precision:.3f}, "
        f"recall={run.aggregate_metrics.macro_recall:.3f}, "
        f"f1={run.aggregate_metrics.macro_f1:.3f}"
    )
    lines.append(
        "- Intent completeness: "
        f"micro={run.aggregate_metrics.micro_intent_completeness:.3f}, "
        f"macro={run.aggregate_metrics.macro_intent_completeness:.3f}"
    )
    lines.append(
        "- Label agreement (micro): "
        f"category={run.aggregate_metrics.micro_category_accuracy:.3f}, "
        f"resolvability={run.aggregate_metrics.micro_resolvability_accuracy:.3f}, "
        f"importance={run.aggregate_metrics.micro_importance_accuracy:.3f}"
    )
    lines.append(
        "- Error taxonomy totals: "
        f"missing={run.aggregate_metrics.total_missing}, "
        f"hallucinated={run.aggregate_metrics.total_hallucinated}, "
        f"hallucination_rate={run.aggregate_metrics.hallucination_rate*100:.1f}%, "
        f"critical_recall={run.aggregate_metrics.critical_recall:.3f}, "
        f"performance_range={run.aggregate_metrics.performance_range:.3f}, "
        f"misclassified={run.aggregate_metrics.total_misclassified}, "
        f"vague_non_resolvable={run.aggregate_metrics.total_vague_non_resolvable}"
    )
    lines.append("")
    lines.append("## Per-Request Table")
    lines.append(
        "| request_id | gold | pred | matched | precision | recall | f1 | "
        "intent_completeness | missing | hallucinated | misclassified | vague_non_resolvable |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for item in run.request_metrics:
        lines.append(
            f"| {item.request_id} | {item.gold_count} | {item.pred_count} | {item.matched_count} | "
            f"{item.precision:.3f} | {item.recall:.3f} | {item.f1:.3f} | "
            f"{item.intent_completeness:.3f} | {item.missing_count} | {item.hallucinated_count} | "
            f"{item.misclassified_count} | {item.vague_non_resolvable_count} |"
        )

    if run.missing_prediction_ids:
        lines.append("")
        lines.append("## Missing Prediction IDs")
        for rid in run.missing_prediction_ids:
            lines.append(f"- {rid}")

    if run.extra_prediction_ids:
        lines.append("")
        lines.append("## Extra Prediction IDs")
        for rid in run.extra_prediction_ids:
            lines.append(f"- {rid}")

    if run.warnings:
        lines.append("")
        lines.append("## Warnings")
        for warning in run.warnings:
            lines.append(f"- {warning}")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_run_artifacts(
    output_root: Path,
    run: RunResult,
    generated_at: str,
    run_config: RunConfig,
) -> Dict[str, Path]:
    """Write CSV/JSON/Markdown artifacts for a single domain-method run."""
    run_dir = output_root / run.domain / run.method
    run_dir.mkdir(parents=True, exist_ok=True)

    csv_path = run_dir / "per_request_metrics.csv"
    json_path = run_dir / "summary.json"
    md_path = run_dir / "summary.md"

    write_per_request_csv(csv_path, run.request_metrics)
    write_json_summary(json_path, run, generated_at, run_config)
    write_markdown_summary(md_path, run, generated_at, run_config)

    return {
        "csv": csv_path,
        "json": json_path,
        "markdown": md_path,
    }


def write_domain_method_comparison(output_root: Path, domain: str, runs: List[RunResult], generated_at: str) -> Dict[str, Path]:
    """Write comparison files across methods for one domain."""
    runs_for_domain = list(runs)
    f1_values = [run.aggregate_metrics.micro_f1 for run in runs_for_domain]
    domain_range = max(f1_values) - min(f1_values) if len(f1_values) > 1 else 0.0
    for run in runs_for_domain:
        run.aggregate_metrics.performance_range = domain_range

    comparison_dir = output_root / "comparisons"
    comparison_dir.mkdir(parents=True, exist_ok=True)

    csv_path = comparison_dir / f"{domain}_method_comparison.csv"
    json_path = comparison_dir / f"{domain}_method_comparison.json"
    md_path = comparison_dir / f"{domain}_method_comparison.md"

    # CSV
    csv_fields = [
        "domain",
        "method",
        "requests_evaluated",
        "micro_precision",
        "micro_recall",
        "micro_f1",
        "micro_intent_completeness",
        "macro_precision",
        "macro_recall",
        "macro_f1",
        "macro_intent_completeness",
        "total_missing",
        "total_hallucinated",
        "hallucination_rate",
        "critical_recall",
        "performance_range",
        "total_misclassified",
        "total_vague_non_resolvable",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=csv_fields)
        writer.writeheader()
        for run in runs:
            writer.writerow(
                {
                    "domain": run.domain,
                    "method": run.method,
                    "requests_evaluated": run.aggregate_metrics.requests_evaluated,
                    "micro_precision": run.aggregate_metrics.micro_precision,
                    "micro_recall": run.aggregate_metrics.micro_recall,
                    "micro_f1": run.aggregate_metrics.micro_f1,
                    "micro_intent_completeness": run.aggregate_metrics.micro_intent_completeness,
                    "macro_precision": run.aggregate_metrics.macro_precision,
                    "macro_recall": run.aggregate_metrics.macro_recall,
                    "macro_f1": run.aggregate_metrics.macro_f1,
                    "macro_intent_completeness": run.aggregate_metrics.macro_intent_completeness,
                    "total_missing": run.aggregate_metrics.total_missing,
                    "total_hallucinated": run.aggregate_metrics.total_hallucinated,
                    "hallucination_rate": round(run.aggregate_metrics.hallucination_rate, 3),
                    "critical_recall": round(run.aggregate_metrics.critical_recall, 3),
                    "performance_range": round(run.aggregate_metrics.performance_range, 3),
                    "total_misclassified": run.aggregate_metrics.total_misclassified,
                    "total_vague_non_resolvable": run.aggregate_metrics.total_vague_non_resolvable,
                }
            )

    # JSON
    payload = {
        "generated_at": generated_at,
        "domain": domain,
        "methods": [
            {
                "method": run.method,
                "aggregate_metrics": aggregate_metrics_to_dict(run.aggregate_metrics),
            }
            for run in runs
        ],
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Markdown
    lines: List[str] = []
    lines.append(f"# Method Comparison: {domain}")
    lines.append("")
    lines.append(f"Generated at: {generated_at}")
    lines.append("")
    lines.append(
        "| method | micro_f1 | macro_f1 | micro_intent_completeness | macro_intent_completeness | "
        "missing | hallucinated | hallucination_rate | critical_recall | performance_range | misclassified | vague_non_resolvable |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for run in runs:
        agg = run.aggregate_metrics
        lines.append(
            f"| {run.method} | {agg.micro_f1:.3f} | {agg.macro_f1:.3f} | "
            f"{agg.micro_intent_completeness:.3f} | {agg.macro_intent_completeness:.3f} | "
            f"{agg.total_missing} | {agg.total_hallucinated} | {agg.hallucination_rate*100:.1f}% | "
            f"{agg.critical_recall:.3f} | {agg.performance_range:.3f} | {agg.total_misclassified} | "
            f"{agg.total_vague_non_resolvable} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "csv": csv_path,
        "json": json_path,
        "markdown": md_path,
    }


def evaluate_acceptance_policy(runs: List[RunResult], run_config: RunConfig) -> AcceptanceSummary:
    """Phase 5 acceptance checks that can fail the process with deterministic rules."""
    total_warnings = sum(len(run.warnings) for run in runs)
    total_missing_predictions = sum(len(run.missing_prediction_ids) for run in runs)
    total_extra_predictions = sum(len(run.extra_prediction_ids) for run in runs)

    if run_config.warnings_as_errors and total_warnings > 0:
        raise EvaluationError(
            "Acceptance check failed: warnings were produced and --warnings-as-errors is enabled.",
            ExitCode.ACCEPTANCE_FAILED,
        )

    if run_config.require_complete_predictions and total_missing_predictions > 0:
        raise EvaluationError(
            "Acceptance check failed: missing predictions detected while --require-complete-predictions is enabled.",
            ExitCode.ACCEPTANCE_FAILED,
        )

    return AcceptanceSummary(
        total_warnings=total_warnings,
        total_missing_predictions=total_missing_predictions,
        total_extra_predictions=total_extra_predictions,
    )


def resolve_rq2_root(base_dir_arg: Optional[str]) -> Path:
    """
    Resolve RQ2 root directory.

    If base-dir is passed, use it directly.
    Otherwise infer RQ2 root from this file path: RQ2/eval/evaluate_rq2.py -> RQ2.
    """
    if base_dir_arg:
        root = Path(base_dir_arg).expanduser().resolve()
    else:
        root = Path(__file__).resolve().parents[1]

    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"RQ2 base directory not found: {root}")
    return root


def normalize_label(value: Any) -> str:
    """Normalize label fields conservatively for exact-lookup comparisons."""
    if not isinstance(value, str):
        return ""
    return " ".join(value.strip().lower().replace("_", "-").split())


def normalize_constraint_text(text: Any, domain: str) -> str:
    """
    Lightweight normalization for short constraint descriptions.

    Notes:
    - Keep this conservative for thesis defensibility.
    - We avoid heavy rewriting and keep content words intact.
    - A tiny domain-specific map is used only for very common surface variants.
    """
    if not isinstance(text, str):
        return ""

    normalized = unicodedata.normalize("NFKC", text).lower().strip()

    # Domain-aware but minimal substitutions observed frequently in these datasets.
    domain_replacements: Dict[str, Dict[str, str]] = {
        "travel": {
            "kms": "km",
            "kilometres": "kilometers",
            "lay overs": "layovers",
        },
        "healthcare": {
            "post op": "post-op",
            "wheel chair": "wheelchair",
        },
    }
    for src, dst in domain_replacements.get(domain, {}).items():
        normalized = normalized.replace(src, dst)

    normalized = normalized.replace("_", " ").replace("-", " ")
    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def tokenize_normalized_text(text: str) -> List[str]:
    """Tokenize by spaces after normalization (no stemming or lemmatization in Phase 2)."""
    if not text:
        return []
    return text.split()


def lexical_similarity(gold_text: str, pred_text: str) -> float:
    """
    Deterministic lexical similarity for short constraints.

    We combine token-level overlap (Jaccard) and character-sequence ratio.
    This stays local, reproducible, and does not depend on external models.
    """
    if not gold_text or not pred_text:
        return 0.0

    gold_tokens = set(tokenize_normalized_text(gold_text))
    pred_tokens = set(tokenize_normalized_text(pred_text))

    if not gold_tokens and not pred_tokens:
        token_jaccard = 1.0
    elif not gold_tokens or not pred_tokens:
        token_jaccard = 0.0
    else:
        token_jaccard = len(gold_tokens & pred_tokens) / len(gold_tokens | pred_tokens)

    seq_ratio = difflib.SequenceMatcher(None, gold_text, pred_text).ratio()
    return 0.6 * token_jaccard + 0.4 * seq_ratio


def align_constraints_greedy(
    gold_constraints: List[Dict[str, Any]],
    pred_constraints: List[Dict[str, Any]],
    domain: str,
    match_threshold: float,
    category_bonus: float,
) -> AlignmentResult:
    """
    Deterministic one-to-one alignment using sorted candidate pairs + greedy selection.

    Process:
    1) Build all candidate pairs with score >= threshold.
    2) Sort by score descending, then gold index, then pred index (stable tie-break).
    3) Select pairs greedily while keeping one-to-one mapping.
    """
    candidate_pairs: List[MatchedPair] = []

    for g_idx, gold_item in enumerate(gold_constraints):
        gold_desc = normalize_constraint_text(gold_item.get("description", ""), domain)
        gold_cat = normalize_label(gold_item.get("category", ""))

        for p_idx, pred_item in enumerate(pred_constraints):
            pred_desc = normalize_constraint_text(pred_item.get("description", ""), domain)
            pred_cat = normalize_label(pred_item.get("category", ""))

            base_similarity = lexical_similarity(gold_desc, pred_desc)
            bonus = category_bonus if gold_cat and pred_cat and gold_cat == pred_cat else 0.0
            score = base_similarity + bonus

            if score >= match_threshold:
                candidate_pairs.append(
                    MatchedPair(
                        gold_index=g_idx,
                        pred_index=p_idx,
                        score=score,
                        base_similarity=base_similarity,
                        category_bonus_applied=bonus,
                    )
                )

    # Deterministic ordering for reproducibility.
    candidate_pairs.sort(key=lambda p: (-p.score, p.gold_index, p.pred_index))

    matched_gold: set[int] = set()
    matched_pred: set[int] = set()
    matches: List[MatchedPair] = []

    for pair in candidate_pairs:
        if pair.gold_index in matched_gold or pair.pred_index in matched_pred:
            continue
        matches.append(pair)
        matched_gold.add(pair.gold_index)
        matched_pred.add(pair.pred_index)

    unmatched_gold = [idx for idx in range(len(gold_constraints)) if idx not in matched_gold]
    unmatched_pred = [idx for idx in range(len(pred_constraints)) if idx not in matched_pred]

    return AlignmentResult(matches=matches, unmatched_gold=unmatched_gold, unmatched_pred=unmatched_pred)


def debug_print_alignment(
    request_id: str,
    gold_constraints: List[Dict[str, Any]],
    pred_constraints: List[Dict[str, Any]],
    result: AlignmentResult,
) -> None:
    """Debug-only alignment view to make matching behavior inspectable request-by-request."""
    print(f"[debug] alignment for {request_id}")
    print(f"[debug]   gold constraints: {len(gold_constraints)}")
    print(f"[debug]   predicted constraints: {len(pred_constraints)}")
    print(f"[debug]   matched pairs: {len(result.matches)}")

    for pair in result.matches:
        gold_desc = gold_constraints[pair.gold_index].get("description", "")
        pred_desc = pred_constraints[pair.pred_index].get("description", "")
        print(
            "[debug]     match "
            f"G{pair.gold_index + 1}<->P{pair.pred_index + 1} "
            f"score={pair.score:.3f} base={pair.base_similarity:.3f} bonus={pair.category_bonus_applied:.3f}"
        )
        print(f"[debug]       gold: {gold_desc}")
        print(f"[debug]       pred: {pred_desc}")

    if result.unmatched_gold:
        print("[debug]   unmatched gold constraints:")
        for idx in result.unmatched_gold:
            print(f"[debug]     G{idx + 1}: {gold_constraints[idx].get('description', '')}")

    if result.unmatched_pred:
        print("[debug]   unmatched predicted constraints:")
        for idx in result.unmatched_pred:
            print(f"[debug]     P{idx + 1}: {pred_constraints[idx].get('description', '')}")


def normalize_domain(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "all":
        return "all"
    canonical = DOMAIN_ALIASES.get(normalized)
    if not canonical:
        raise ValueError(f"Unsupported domain: {value}")
    return canonical


def normalize_method(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "all":
        return "all"
    canonical = METHOD_ALIASES.get(normalized)
    if not canonical:
        raise ValueError(f"Unsupported method: {value}")
    return canonical


def get_domain_config(domain: str) -> DomainConfig:
    if domain == "travel":
        return DomainConfig(
            canonical_name="travel",
            gold_file_candidates=["annotations_travel_gold.json"],
            subset_file_candidates=["travel_subset.json", "travelrequests_subset.json"],
            prediction_subdir="travel",
        )
    if domain == "healthcare":
        return DomainConfig(
            canonical_name="healthcare",
            gold_file_candidates=["annotations_healthcare_gold.json"],
            subset_file_candidates=["healthcare_subset.json", "healthcarerequests_subset.json"],
            prediction_subdir="healthcare",
        )
    raise ValueError(f"Unsupported canonical domain: {domain}")


def resolve_first_existing(base_dir: Path, file_candidates: List[str]) -> Tuple[Optional[Path], List[Path]]:
    """Return first existing candidate path plus all checked candidate paths for transparency."""
    checked_paths = [base_dir / candidate for candidate in file_candidates]
    for path in checked_paths:
        if path.exists() and path.is_file():
            return path, checked_paths
    return None, checked_paths


def resolve_method_folder(root: Path, method: str) -> Tuple[Path, List[Path]]:
    """
    Resolve a method folder with light alias support.

    We keep canonical names but allow common legacy naming styles in the project folders.
    """
    method_folder_candidates: Dict[str, List[str]] = {
        "zeroshot": ["zeroshot", "zero_shot", "Zero_Shot"],
        "fewshot": ["fewshot", "few_shot", "Few_Shot"],
        "cot": ["cot", "CoT", "reasoning"],
        "hybrid": ["hybrid", "Hybrid"],
    }

    checked_paths: List[Path] = []
    for folder_name in method_folder_candidates[method]:
        candidate = root / folder_name
        checked_paths.append(candidate)
        if candidate.exists() and candidate.is_dir():
            return candidate, checked_paths

    # If no folder exists yet, still return canonical location for deterministic reporting.
    canonical_default = root / method
    checked_paths.append(canonical_default)
    return canonical_default, checked_paths


def resolve_prediction_folder(
    method_folder: Path,
    method: str,
    domain_cfg: DomainConfig,
    hybrid_source: str,
) -> Tuple[Path, List[Path]]:
    """
    Resolve prediction folder path for a method/domain.

    We keep this deterministic and transparent by checking a short ordered list of folders.
    """
    domain_dir = domain_cfg.prediction_subdir
    checked_paths: List[Path] = []

    if method == "hybrid":
        if hybrid_source == "validator":
            candidates = [
                method_folder / "validator_outputs" / domain_dir,
                method_folder / "llm_outputs" / domain_dir,
            ]
        else:
            candidates = [
                method_folder / "llm_outputs" / domain_dir,
                method_folder / "validator_outputs" / domain_dir,
            ]
    else:
        candidates = [
            method_folder / "llm_outputs" / domain_dir,
            method_folder / domain_dir,
            method_folder / "outputs" / domain_dir,
        ]

    for path in candidates:
        checked_paths.append(path)
        if path.exists() and path.is_dir():
            return path, checked_paths

    # Folder may not exist yet in early setup; return preferred first candidate for dry-run visibility.
    return candidates[0], checked_paths


def load_json_file(path: Path) -> Any:
    """Load JSON with clear errors so bad files are easy to debug."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Could not read file: {path} ({exc})") from exc

    if not text.strip():
        raise ValueError(
            f"Invalid JSON in {path}: file is empty or whitespace-only. "
            "Please save valid JSON content before running evaluation."
        )

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {path}: {exc}. "
            "Please fix the JSON syntax and save the file."
        ) from exc


def load_gold_requests(gold_path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load gold file and index by request_id.

    This function validates only fields needed in Phase 1 loading checks.
    """
    payload = load_json_file(gold_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Gold file must be a JSON object: {gold_path}")

    annotations = payload.get("annotations")
    if not isinstance(annotations, list):
        raise ValueError(f"Gold file must contain an 'annotations' list: {gold_path}")

    by_id: Dict[str, Dict[str, Any]] = {}
    for idx, item in enumerate(annotations, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Gold annotation #{idx} is not an object in {gold_path}")

        request_id = item.get("request_id")
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError(f"Gold annotation #{idx} missing valid request_id in {gold_path}")

        constraints = item.get("constraints")
        if not isinstance(constraints, list):
            raise ValueError(
                f"Gold annotation {request_id} missing constraints list in {gold_path}"
            )

        if request_id in by_id:
            raise ValueError(f"Duplicate request_id in gold file: {request_id} ({gold_path})")
        by_id[request_id] = item

    return by_id


def load_subset_ids(
    subset_path: Path,
    allow_subset_fallback: bool,
    gold_by_id: Dict[str, Dict[str, Any]],
) -> Tuple[List[str], List[str]]:
    """
    Load subset request IDs from subset JSON.

    Returns tuple: (subset_ids, warnings)
    """
    warnings: List[str] = []

    if not subset_path.exists():
        if allow_subset_fallback:
            warnings.append(
                f"Subset file missing, fallback enabled -> using all gold request IDs: {subset_path}"
            )
            return sorted(gold_by_id.keys()), warnings
        raise FileNotFoundError(
            f"Subset file not found: {subset_path}. "
            "Use --allow-subset-fallback only if this is intentional."
        )

    payload = load_json_file(subset_path)
    if not isinstance(payload, dict):
        raise ValueError(f"Subset file must be a JSON object: {subset_path}")

    requests = payload.get("requests")
    if not isinstance(requests, list):
        raise ValueError(f"Subset file must contain a 'requests' list: {subset_path}")

    subset_ids: List[str] = []
    seen: set[str] = set()

    for idx, item in enumerate(requests, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Subset entry #{idx} is not an object in {subset_path}")

        request_id = item.get("request_id")
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError(f"Subset entry #{idx} missing valid request_id in {subset_path}")

        if request_id in seen:
            raise ValueError(f"Duplicate request_id in subset file: {request_id} ({subset_path})")
        seen.add(request_id)
        subset_ids.append(request_id)

    # Early warning for potential subset/gold mismatch.
    missing_in_gold = [rid for rid in subset_ids if rid not in gold_by_id]
    if missing_in_gold:
        warnings.append(
            "Subset contains request IDs not found in gold: " + ", ".join(missing_in_gold)
        )

    return subset_ids, warnings


def validate_prediction_schema(payload: Any, source_file: Path) -> None:
    """
    Strict validation for prediction JSON structure.

    request_id is optional in JSON because filename fallback is allowed,
    but constraints and key fields are required.
    """
    if not isinstance(payload, dict):
        raise ValueError(f"Prediction must be a JSON object: {source_file}")

    if "request_id" in payload:
        request_id = payload.get("request_id")
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValueError(f"Prediction has invalid request_id in {source_file}")

    constraints = payload.get("constraints")
    if not isinstance(constraints, list):
        raise ValueError(f"Prediction must contain constraints list: {source_file}")

    required_fields = ["description", "category", "resolvability", "importance"]

    for idx, constraint in enumerate(constraints, start=1):
        if not isinstance(constraint, dict):
            raise ValueError(f"Constraint #{idx} is not an object in {source_file}")
        for field in required_fields:
            value = constraint.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Constraint #{idx} missing valid '{field}' in {source_file}"
                )


def derive_request_id_from_filename(path: Path) -> str:
    """Filename fallback when prediction JSON does not include request_id."""
    stem = path.stem.strip()
    if not stem:
        raise ValueError(f"Could not derive request_id from filename: {path}")
    return stem


def load_predictions(
    prediction_dir: Path,
    debug: bool,
) -> Tuple[Dict[str, LoadedPrediction], List[str], int]:
    """
    Load all prediction JSON files in the resolved folder.

    Returns:
    - dict keyed by request_id
    - warnings list
    - number of prediction files discovered
    """
    warnings: List[str] = []

    if not prediction_dir.exists() or not prediction_dir.is_dir():
        warnings.append(f"Prediction folder not found (count treated as 0): {prediction_dir}")
        return {}, warnings, 0

    json_files = sorted(prediction_dir.glob("*.json"))
    predictions_by_id: Dict[str, LoadedPrediction] = {}

    for file_path in json_files:
        payload = load_json_file(file_path)

        # Phase 1 rule: prediction schema validation is always strict.
        validate_prediction_schema(payload, file_path)

        request_id = payload.get("request_id")
        if not isinstance(request_id, str) or not request_id.strip():
            request_id = derive_request_id_from_filename(file_path)
            if debug:
                warnings.append(
                    f"Prediction request_id missing in {file_path.name}; using filename fallback '{request_id}'"
                )

        if request_id in predictions_by_id:
            existing = predictions_by_id[request_id].source_file
            raise ValueError(
                "Duplicate prediction request_id detected: "
                f"{request_id} in {existing} and {file_path}"
            )

        predictions_by_id[request_id] = LoadedPrediction(
            request_id=request_id,
            source_file=file_path,
            payload=payload,
        )

    return predictions_by_id, warnings, len(json_files)


def print_dry_run_summary(
    domain: str,
    method: str,
    gold_path: Path,
    subset_path: Path,
    prediction_path: Path,
    subset_count: int,
    gold_count: int,
    prediction_file_count: int,
    total_alignment_matches: int,
    request_metrics: List[RequestMetrics],
    aggregate_metrics: AggregateMetrics,
    missing_prediction_ids: List[str],
    extra_prediction_ids: List[str],
    warnings: List[str],
) -> None:
    """Human-readable summary for quick inspection before scoring logic is added."""
    print("=" * 80)
    print("RQ2 Phase 1-3 Console Summary")
    print("=" * 80)
    print(f"selected domain: {domain}")
    print(f"selected method: {method}")
    print(f"resolved gold file path: {gold_path}")
    print(f"resolved subset file path: {subset_path}")
    print(f"resolved prediction folder path: {prediction_path}")
    print(f"number of subset requests loaded: {subset_count}")
    print(f"number of gold requests loaded: {gold_count}")
    print(f"number of prediction files found: {prediction_file_count}")
    print(f"phase 2 total aligned pairs (all subset requests): {total_alignment_matches}")
    print("")
    print("phase 3 per-request metrics:")
    for item in request_metrics:
        print(
            f"  - {item.request_id}: "
            f"gold={item.gold_count}, pred={item.pred_count}, matched={item.matched_count}, "
            f"precision={item.precision:.3f}, recall={item.recall:.3f}, f1={item.f1:.3f}, "
            f"intent_completeness={item.intent_completeness:.3f}, "
            f"missing={item.missing_count}, hallucinated={item.hallucinated_count}, "
            f"misclassified={item.misclassified_count}, vague_non_resolvable={item.vague_non_resolvable_count}"
        )

    print("")
    print("phase 3 aggregate metrics:")
    print(f"  requests evaluated: {aggregate_metrics.requests_evaluated}")
    print(
        "  micro extraction: "
        f"precision={aggregate_metrics.micro_precision:.3f}, "
        f"recall={aggregate_metrics.micro_recall:.3f}, "
        f"f1={aggregate_metrics.micro_f1:.3f}"
    )
    print(
        "  macro extraction: "
        f"precision={aggregate_metrics.macro_precision:.3f}, "
        f"recall={aggregate_metrics.macro_recall:.3f}, "
        f"f1={aggregate_metrics.macro_f1:.3f}"
    )
    print(
        "  intent completeness: "
        f"micro={aggregate_metrics.micro_intent_completeness:.3f}, "
        f"macro={aggregate_metrics.macro_intent_completeness:.3f}"
    )
    print(
        "  label agreement micro: "
        f"category={aggregate_metrics.micro_category_accuracy:.3f}, "
        f"resolvability={aggregate_metrics.micro_resolvability_accuracy:.3f}, "
        f"importance={aggregate_metrics.micro_importance_accuracy:.3f}"
    )
    print(
        "  label agreement macro: "
        f"category={aggregate_metrics.macro_category_accuracy:.3f}, "
        f"resolvability={aggregate_metrics.macro_resolvability_accuracy:.3f}, "
        f"importance={aggregate_metrics.macro_importance_accuracy:.3f}"
    )
    print(
        "  taxonomy totals: "
        f"missing={aggregate_metrics.total_missing}, "
        f"hallucinated={aggregate_metrics.total_hallucinated}, "
        f"hall_rate={aggregate_metrics.hallucination_rate:.2f}, "
        f"critical_recall={aggregate_metrics.critical_recall:.3f}, "
        f"misclassified={aggregate_metrics.total_misclassified}, "
        f"vague_non_resolvable={aggregate_metrics.total_vague_non_resolvable}"
    )

    print("request IDs missing predictions:")
    if missing_prediction_ids:
        for rid in missing_prediction_ids:
            print(f"  - {rid}")
    else:
        print("  - none")

    print("extra prediction files not in subset:")
    if extra_prediction_ids:
        for rid in extra_prediction_ids:
            print(f"  - {rid}")
    else:
        print("  - none")

    if warnings:
        print("warnings:")
        for warning in warnings:
            print(f"  - {warning}")


def inspect_one_domain_method(
    root: Path,
    domain: str,
    method: str,
    hybrid_source: str,
    allow_subset_fallback: bool,
    match_threshold: float,
    category_bonus: float,
    debug: bool,
) -> RunResult:
    """Inspect one domain/method combination for Phase 1-3 readiness."""
    domain_cfg = get_domain_config(domain)
    data_dir = root / "data"

    gold_path, gold_checked = resolve_first_existing(data_dir, domain_cfg.gold_file_candidates)
    if not gold_path:
        checked = "\n".join(str(path) for path in gold_checked)
        raise FileNotFoundError(
            f"Could not resolve gold file for domain '{domain}'. Checked:\n{checked}"
        )

    subset_path, subset_checked = resolve_first_existing(data_dir, domain_cfg.subset_file_candidates)
    if not subset_path:
        # We still create deterministic path for reporting/error text.
        subset_path = data_dir / domain_cfg.subset_file_candidates[0]
        if debug:
            print("[debug] subset file candidates checked:")
            for path in subset_checked:
                print(f"[debug]   {path}")

    method_folder, method_checked = resolve_method_folder(root, method)
    prediction_folder, prediction_checked = resolve_prediction_folder(
        method_folder=method_folder,
        method=method,
        domain_cfg=domain_cfg,
        hybrid_source=hybrid_source,
    )

    if debug:
        print("[debug] method folder candidates checked:")
        for path in method_checked:
            print(f"[debug]   {path}")
        print("[debug] prediction folder candidates checked:")
        for path in prediction_checked:
            print(f"[debug]   {path}")

    gold_by_id = load_gold_requests(gold_path)
    subset_ids, subset_warnings = load_subset_ids(
        subset_path=subset_path,
        allow_subset_fallback=allow_subset_fallback,
        gold_by_id=gold_by_id,
    )

    predictions_by_id, prediction_warnings, prediction_file_count = load_predictions(
        prediction_dir=prediction_folder,
        debug=debug,
    )

    # Phase 2+3: run deterministic alignment and compute request-level metrics.
    total_alignment_matches = 0
    request_metrics: List[RequestMetrics] = []
    for request_id in subset_ids:
        gold_entry = gold_by_id.get(request_id)
        if not gold_entry:
            # Keep going so one subset/gold mismatch does not block inspection for all requests.
            continue

        gold_constraints = gold_entry.get("constraints", [])
        prediction_payload = predictions_by_id.get(request_id)
        pred_constraints = (
            prediction_payload.payload.get("constraints", []) if prediction_payload else []
        )

        alignment_result = align_constraints_greedy(
            gold_constraints=gold_constraints,
            pred_constraints=pred_constraints,
            domain=domain,
            match_threshold=match_threshold,
            category_bonus=category_bonus,
        )
        total_alignment_matches += len(alignment_result.matches)

        request_metric = compute_request_metrics(
            request_id=request_id,
            domain=domain,
            gold_constraints=gold_constraints,
            pred_constraints=pred_constraints,
            alignment_result=alignment_result,
        )
        request_metrics.append(request_metric)

        if debug:
            debug_print_alignment(
                request_id=request_id,
                gold_constraints=gold_constraints,
                pred_constraints=pred_constraints,
                result=alignment_result,
            )
            print(
                "[debug]   request metrics: "
                f"precision={request_metric.precision:.3f}, "
                f"recall={request_metric.recall:.3f}, "
                f"f1={request_metric.f1:.3f}, "
                f"intent_completeness={request_metric.intent_completeness:.3f}, "
                f"misclassified={request_metric.misclassified_count}"
            )

    aggregate_metrics = aggregate_request_metrics(request_metrics)

    subset_set = set(subset_ids)
    prediction_set = set(predictions_by_id.keys())

    missing_prediction_ids = sorted(subset_set - prediction_set)
    extra_prediction_ids = sorted(prediction_set - subset_set)

    all_warnings = subset_warnings + prediction_warnings

    print_dry_run_summary(
        domain=domain,
        method=method,
        gold_path=gold_path,
        subset_path=subset_path,
        prediction_path=prediction_folder,
        subset_count=len(subset_ids),
        gold_count=len(gold_by_id),
        prediction_file_count=prediction_file_count,
        total_alignment_matches=total_alignment_matches,
        request_metrics=request_metrics,
        aggregate_metrics=aggregate_metrics,
        missing_prediction_ids=missing_prediction_ids,
        extra_prediction_ids=extra_prediction_ids,
        warnings=all_warnings,
    )

    return RunResult(
        domain=domain,
        method=method,
        gold_path=gold_path,
        subset_path=subset_path,
        prediction_path=prediction_folder,
        subset_count=len(subset_ids),
        gold_count=len(gold_by_id),
        prediction_file_count=prediction_file_count,
        total_alignment_matches=total_alignment_matches,
        request_metrics=request_metrics,
        aggregate_metrics=aggregate_metrics,
        missing_prediction_ids=missing_prediction_ids,
        extra_prediction_ids=extra_prediction_ids,
        warnings=all_warnings,
    )


def expand_domains(domain_arg: str) -> List[str]:
    if domain_arg == "all":
        return ["travel", "healthcare"]
    return [domain_arg]


def expand_methods(method_arg: str) -> List[str]:
    if method_arg == "all":
        return list(CANONICAL_METHODS)
    return [method_arg]


def main() -> int:
    parser = build_cli_parser()
    args = parser.parse_args()

    try:
        domain = normalize_domain(args.domain)
        method = normalize_method(args.method)

        run_config = RunConfig(
            match_threshold=args.match_threshold,
            category_bonus=args.category_bonus,
            hybrid_source=args.hybrid_source,
            allow_subset_fallback=args.allow_subset_fallback,
            warnings_as_errors=args.warnings_as_errors,
            require_complete_predictions=args.require_complete_predictions,
        )
        validate_phase2_args(run_config.match_threshold, run_config.category_bonus)
        validate_run_config(run_config)

        root = resolve_rq2_root(args.base_dir)
        output_root = resolve_output_root(root, args.output_dir)
        generated_at = datetime.now().isoformat(timespec="seconds")

        selected_domains = expand_domains(domain)
        selected_methods = expand_methods(method)

        all_run_results: List[RunResult] = []

        for selected_domain in selected_domains:
            for selected_method in selected_methods:
                run_result = inspect_one_domain_method(
                    root=root,
                    domain=selected_domain,
                    method=selected_method,
                    hybrid_source=run_config.hybrid_source,
                    allow_subset_fallback=run_config.allow_subset_fallback,
                    match_threshold=run_config.match_threshold,
                    category_bonus=run_config.category_bonus,
                    debug=args.debug,
                )
                all_run_results.append(run_result)

                artifact_paths = write_run_artifacts(
                    output_root=output_root,
                    run=run_result,
                    generated_at=generated_at,
                    run_config=run_config,
                )
                print("")
                print("phase 4 artifacts written:")
                print(f"  - csv: {artifact_paths['csv']}")
                print(f"  - json: {artifact_paths['json']}")
                print(f"  - markdown: {artifact_paths['markdown']}")

        # If multiple methods were evaluated for the same domain, also write a comparison view.
        runs_by_domain: Dict[str, List[RunResult]] = {}
        for run in all_run_results:
            runs_by_domain.setdefault(run.domain, []).append(run)

        for domain_name, runs in runs_by_domain.items():
            unique_methods = sorted({run.method for run in runs})
            if len(unique_methods) <= 1:
                continue

            comparison_paths = write_domain_method_comparison(
                output_root=output_root,
                domain=domain_name,
                runs=sorted(runs, key=lambda r: r.method),
                generated_at=generated_at,
            )
            print("")
            print(f"phase 4 comparison artifacts written for domain '{domain_name}':")
            print(f"  - csv: {comparison_paths['csv']}")
            print(f"  - json: {comparison_paths['json']}")
            print(f"  - markdown: {comparison_paths['markdown']}")

        acceptance = evaluate_acceptance_policy(all_run_results, run_config)
        print("")
        print("phase 5 acceptance summary:")
        print(f"  - total warnings: {acceptance.total_warnings}")
        print(f"  - total missing predictions: {acceptance.total_missing_predictions}")
        print(f"  - total extra predictions: {acceptance.total_extra_predictions}")
        return int(ExitCode.SUCCESS)

    except EvaluationError as exc:
        print(f"ERROR: {exc}")
        return int(exc.exit_code)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return int(ExitCode.DATA_ERROR)
    except json.JSONDecodeError as exc:
        print(f"ERROR: Invalid JSON: {exc}")
        return int(ExitCode.VALIDATION_ERROR)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return int(ExitCode.VALIDATION_ERROR)
    except Exception as exc:
        print(f"ERROR: Unexpected failure: {exc}")
        return int(ExitCode.UNEXPECTED_ERROR)


if __name__ == "__main__":
    sys.exit(main())
