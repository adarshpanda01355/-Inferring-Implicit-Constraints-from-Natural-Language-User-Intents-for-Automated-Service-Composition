#!/usr/bin/env python3
"""
Generate LLM outputs for RQ2 subsets across prompting methods.

Key guarantees:
- Uses canonical evaluator paths: <method>/llm_outputs/<domain>/<REQUEST_ID>.json
- Replaces only {request_id} and {request_text} placeholders in prompt templates
- Stores invalid/non-JSON model outputs outside llm_outputs in llm_raw_failures
- Supports dry-check mode to validate paths, placeholders, routing, and subset integrity
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from openai import OpenAI


CANONICAL_METHODS = ["zeroshot", "fewshot", "cot", "hybrid"]
CANONICAL_DOMAINS = ["travel", "healthcare"]
EXPECTED_PER_DOMAIN = 10

PROMPT_PATHS = {
    "zeroshot": Path("zeroshot") / "zero_shot_prompt.md",
    "fewshot": Path("fewshot") / "few_shot_prompt.md",
    "cot": Path("cot") / "CoT_prompt.md",
    "hybrid": Path("hybrid") / "hybrid_prompt.md",
}

SUBSET_PATHS = {
    "travel": Path("data") / "travelrequests_subset.json",
    "healthcare": Path("data") / "healthcarerequests_subset.json",
}

CONSTRAINT_EXTRACTION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "request_id": {"type": "string"},
        "constraints": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["Temporal", "Spatial", "Domain-default", "Logical"],
                    },
                    "resolvability": {
                        "type": "string",
                        "enum": ["Implicit", "Vague", "Borderline"],
                    },
                    "importance": {
                        "type": "string",
                        "enum": ["Critical", "Useful", "Optional"],
                    },
                    "notes": {"type": "string"},
                },
                "required": [
                    "id",
                    "description",
                    "category",
                    "resolvability",
                    "importance",
                    "notes",
                ],
                "additionalProperties": False,
            },
        },
        "constraint_count": {"type": "integer"},
        "density": {
            "type": "string",
            "enum": ["Low", "Medium", "High"],
        },
    },
    "required": ["request_id", "constraints", "constraint_count", "density"],
    "additionalProperties": False,
}


@dataclass
class RequestItem:
    request_id: str
    request: str


@dataclass
class RunSettings:
    model: str
    temperature: float
    max_output_tokens: int
    timeout_seconds: float
    max_attempts: int


class GenerationError(Exception):
    pass


def parse_selection_arg(value: str, allowed: List[str], arg_name: str) -> List[str]:
    raw = value.strip().lower()
    if raw == "all":
        return list(allowed)

    picked = [part.strip().lower() for part in raw.split(",") if part.strip()]
    if not picked:
        raise GenerationError(f"--{arg_name} cannot be empty")

    invalid = [item for item in picked if item not in allowed]
    if invalid:
        raise GenerationError(
            f"Invalid --{arg_name} values: {', '.join(invalid)}. Allowed: {', '.join(allowed)}"
        )

    # Keep user order but remove duplicates so runs are predictable.
    deduped: List[str] = []
    for item in picked:
        if item not in deduped:
            deduped.append(item)
    return deduped


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise GenerationError(f"Failed to load JSON from {path}: {exc}") from exc


def load_subset(path: Path) -> List[RequestItem]:
    payload = load_json(path)
    if not isinstance(payload, dict) or "requests" not in payload:
        raise GenerationError(f"Subset file has invalid schema: {path}")

    raw_requests = payload.get("requests")
    if not isinstance(raw_requests, list):
        raise GenerationError(f"Subset file 'requests' must be a list: {path}")

    items: List[RequestItem] = []
    for idx, item in enumerate(raw_requests, start=1):
        if not isinstance(item, dict):
            raise GenerationError(f"Subset item #{idx} is not an object in {path}")

        request_id = item.get("request_id")
        request_text = item.get("request")
        if not isinstance(request_id, str) or not request_id.strip():
            raise GenerationError(f"Subset item #{idx} missing valid request_id in {path}")
        if not isinstance(request_text, str) or not request_text.strip():
            raise GenerationError(f"Subset item #{idx} missing valid request in {path}")

        items.append(RequestItem(request_id=request_id.strip(), request=request_text))

    # Return clean request records that are ready for prompt injection.
    return items


def load_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        raise GenerationError(f"Failed to read prompt file {path}: {exc}") from exc


def build_prompt(prompt_template: str, request_id: str, request_text: str) -> str:
    # Only replace the two agreed placeholders to avoid accidental template edits.
    return prompt_template.replace("{request_id}", request_id).replace("{request_text}", request_text)


def has_both_placeholders(prompt_template: str) -> bool:
    return "{request_id}" in prompt_template and "{request_text}" in prompt_template


def ensure_dirs(path_list: List[Path]) -> None:
    for path in path_list:
        path.mkdir(parents=True, exist_ok=True)


def should_retry(error: Exception) -> bool:
    # Small heuristic: retry only on transient failures we commonly see.
    text = str(error).lower()
    transient_markers = [
        "rate limit",
        "429",
        "timeout",
        "timed out",
        "502",
        "503",
        "504",
        "bad gateway",
        "service unavailable",
        "gateway timeout",
    ]
    return any(marker in text for marker in transient_markers)


def call_model_once(client: OpenAI, settings: RunSettings, prompt: str) -> str:
    # Ask the model for strict JSON that matches our evaluator schema.
    response = client.responses.create(
        model=settings.model,
        input=prompt,
        temperature=settings.temperature,
        max_output_tokens=settings.max_output_tokens,
        timeout=settings.timeout_seconds,
        text={
            "format": {
                "type": "json_schema",
                "name": "constraint_extraction",
                "strict": True,
                "schema": CONSTRAINT_EXTRACTION_SCHEMA,
            }
        },
    )
    return response.output_text or ""


def call_model_with_retries(client: OpenAI, settings: RunSettings, prompt: str) -> Tuple[str, int]:
    last_error: Exception | None = None

    for attempt in range(1, settings.max_attempts + 1):
        try:
            text = call_model_once(client, settings, prompt)
            return text, attempt
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= settings.max_attempts or not should_retry(exc):
                raise

            # Exponential backoff + tiny jitter to reduce retry collisions.
            delay = (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            time.sleep(delay)

    if last_error:
        raise last_error
    raise GenerationError("Unexpected retry flow reached")


def parse_model_json(model_text: str) -> Dict[str, Any]:
    parsed = json.loads(model_text)
    if not isinstance(parsed, dict):
        raise ValueError("Model output JSON is not an object")
    return parsed


def normalize_count_density(parsed: Dict[str, Any]) -> Dict[str, Any]:
    # Recompute count/density from constraints so downstream files stay consistent.
    constraints = parsed.get("constraints")
    if not isinstance(constraints, list):
        constraints = []
        parsed["constraints"] = constraints

    count = len(constraints)
    parsed["constraint_count"] = count

    if count <= 2:
        parsed["density"] = "Low"
    elif count <= 4:
        parsed["density"] = "Medium"
    else:
        parsed["density"] = "High"

    return parsed


def method_domain_output_dir(rq2_root: Path, method: str, domain: str) -> Path:
    return rq2_root / method / "llm_outputs" / domain


def method_domain_raw_fail_dir(rq2_root: Path, method: str, domain: str) -> Path:
    return rq2_root / method / "llm_raw_failures" / domain


def validate_subset_integrity(items: List[RequestItem], domain: str) -> List[str]:
    issues: List[str] = []
    ids = [item.request_id for item in items]
    if len(ids) != len(set(ids)):
        issues.append(f"{domain}: duplicate request_id values found")
    if len(items) != EXPECTED_PER_DOMAIN:
        issues.append(
            f"{domain}: expected {EXPECTED_PER_DOMAIN} requests, found {len(items)}"
        )
    return issues


def dry_check(rq2_root: Path, methods: List[str], domains: List[str]) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "checked_at": now_iso(),
        "ok": True,
        "issues": [],
        "details": {
            "methods": {},
            "domains": {},
        },
    }

    for method in methods:
        # Check that each method prompt exists and has both required placeholders.
        prompt_path = rq2_root / PROMPT_PATHS[method]
        method_detail: Dict[str, Any] = {
            "prompt_path": str(prompt_path),
            "prompt_exists": prompt_path.exists(),
            "has_request_id_placeholder": False,
            "has_request_text_placeholder": False,
        }

        if prompt_path.exists():
            prompt_template = load_prompt(prompt_path)
            method_detail["has_request_id_placeholder"] = "{request_id}" in prompt_template
            method_detail["has_request_text_placeholder"] = "{request_text}" in prompt_template
            if not has_both_placeholders(prompt_template):
                report["issues"].append(
                    f"{method}: prompt missing required placeholders at {prompt_path}"
                )

        if not prompt_path.exists():
            report["issues"].append(f"{method}: missing prompt file at {prompt_path}")

        report["details"]["methods"][method] = method_detail

    for domain in domains:
        # Check subset presence and where each method/domain output will be routed.
        subset_path = rq2_root / SUBSET_PATHS[domain]
        domain_detail: Dict[str, Any] = {
            "subset_path": str(subset_path),
            "subset_exists": subset_path.exists(),
            "request_count": 0,
            "duplicate_ids": False,
            "routing": {},
        }

        if not subset_path.exists():
            report["issues"].append(f"{domain}: missing subset file at {subset_path}")
            report["details"]["domains"][domain] = domain_detail
            continue

        items = load_subset(subset_path)
        domain_detail["request_count"] = len(items)
        integ_issues = validate_subset_integrity(items, domain)
        if integ_issues:
            report["issues"].extend(integ_issues)
            domain_detail["duplicate_ids"] = any("duplicate" in issue for issue in integ_issues)

        for method in methods:
            out_dir = method_domain_output_dir(rq2_root, method, domain)
            raw_dir = method_domain_raw_fail_dir(rq2_root, method, domain)
            sample_target = str(out_dir / f"{items[0].request_id}.json") if items else None
            domain_detail["routing"][method] = {
                "output_dir": str(out_dir),
                "output_dir_exists": out_dir.exists(),
                "raw_failure_dir": str(raw_dir),
                "raw_failure_dir_exists": raw_dir.exists(),
                "sample_output_file": sample_target,
            }

        report["details"]["domains"][domain] = domain_detail

    report["ok"] = len(report["issues"]) == 0
    return report


def run_generation(
    rq2_root: Path,
    settings: RunSettings,
    overwrite: bool,
    methods: List[str],
    domains: List[str],
) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise GenerationError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

    summary: Dict[str, Any] = {
        "started_at": now_iso(),
        "model": settings.model,
        "methods": methods,
        "domains": domains,
        "temperature": settings.temperature,
        "max_output_tokens": settings.max_output_tokens,
        "timeout_seconds": settings.timeout_seconds,
        "max_attempts": settings.max_attempts,
        "runs": {},
        "totals": {
            "attempted": 0,
            "saved_json": 0,
            "raw_failures": 0,
            "api_failures": 0,
        },
    }

    for method in methods:
        # Load prompt once per method and reuse it across requests.
        prompt_template = load_prompt(rq2_root / PROMPT_PATHS[method])
        if not has_both_placeholders(prompt_template):
            raise GenerationError(
                f"Prompt file for {method} is missing required placeholders"
            )

        summary["runs"][method] = {}

        for domain in domains:
            items = load_subset(rq2_root / SUBSET_PATHS[domain])
            subset_issues = validate_subset_integrity(items, domain)
            if subset_issues:
                raise GenerationError("; ".join(subset_issues))

            output_dir = method_domain_output_dir(rq2_root, method, domain)
            raw_dir = method_domain_raw_fail_dir(rq2_root, method, domain)
            ensure_dirs([output_dir, raw_dir])

            run_stats: Dict[str, Any] = {
                "attempted": 0,
                "saved_json": 0,
                "raw_failures": 0,
                "api_failures": 0,
                "failed_request_ids": [],
                "records": [],
            }

            for item in items:
                run_stats["attempted"] += 1
                summary["totals"]["attempted"] += 1

                prompt = build_prompt(prompt_template, item.request_id, item.request)
                out_file = output_dir / f"{item.request_id}.json"
                raw_file = raw_dir / f"{item.request_id}.txt"

                if out_file.exists() and not overwrite:
                    # Skip existing outputs unless user explicitly asks to overwrite.
                    run_stats["records"].append(
                        {
                            "request_id": item.request_id,
                            "status": "skipped_existing",
                            "output_file": str(out_file),
                        }
                    )
                    continue

                try:
                    model_text, attempts_used = call_model_with_retries(client, settings, prompt)
                except Exception as exc:  # noqa: BLE001
                    run_stats["api_failures"] += 1
                    summary["totals"]["api_failures"] += 1
                    run_stats["failed_request_ids"].append(item.request_id)
                    run_stats["records"].append(
                        {
                            "request_id": item.request_id,
                            "status": "api_failure",
                            "error": str(exc),
                        }
                    )
                    continue

                try:
                    # Preferred path: valid JSON goes into llm_outputs.
                    parsed = parse_model_json(model_text)
                    parsed = normalize_count_density(parsed)
                    out_file.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
                    run_stats["saved_json"] += 1
                    summary["totals"]["saved_json"] += 1
                    run_stats["records"].append(
                        {
                            "request_id": item.request_id,
                            "status": "saved_json",
                            "attempts_used": attempts_used,
                            "output_file": str(out_file),
                        }
                    )
                except Exception as parse_exc:  # noqa: BLE001
                    # Keep raw text for manual inspection when JSON parsing fails.
                    raw_file.write_text(model_text, encoding="utf-8")
                    run_stats["raw_failures"] += 1
                    summary["totals"]["raw_failures"] += 1
                    run_stats["failed_request_ids"].append(item.request_id)
                    run_stats["records"].append(
                        {
                            "request_id": item.request_id,
                            "status": "raw_failure",
                            "attempts_used": attempts_used,
                            "raw_file": str(raw_file),
                            "parse_error": str(parse_exc),
                        }
                    )

            summary["runs"][method][domain] = run_stats

    summary["finished_at"] = now_iso()
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate RQ2 LLM outputs")
    parser.add_argument(
        "--rq2-root",
        default=None,
        help="Path to RQ2 root folder. Defaults to script parent folder.",
    )
    parser.add_argument(
        "--dry-check",
        action="store_true",
        help="Validate structure and routing only; do not call API.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing JSON output files.",
    )
    parser.add_argument(
        "--methods",
        default="all",
        help=(
            "Comma-separated methods to run (zeroshot,fewshot,cot,hybrid) "
            "or 'all'."
        ),
    )
    parser.add_argument(
        "--domains",
        default="all",
        help="Comma-separated domains to run (travel,healthcare) or 'all'.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-5.4"),
        help="Model name to use for generation.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=float(os.environ.get("OPENAI_TEMPERATURE", "0")),
        help="Sampling temperature.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=int(os.environ.get("OPENAI_MAX_OUTPUT_TOKENS", "1800")),
        help="Max output tokens per request.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "60")),
        help="Timeout in seconds for each API call.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=int(os.environ.get("OPENAI_MAX_ATTEMPTS", "3")),
        help="Max attempts for retryable API failures.",
    )
    parser.add_argument(
        "--report-path",
        default=None,
        help="Optional path for writing dry-check or run summary JSON.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    rq2_root = (
        Path(args.rq2_root).expanduser().resolve()
        if args.rq2_root
        else Path(__file__).resolve().parents[1]
    )

    settings = RunSettings(
        model=args.model,
        temperature=args.temperature,
        max_output_tokens=args.max_output_tokens,
        timeout_seconds=args.timeout_seconds,
        max_attempts=args.max_attempts,
    )

    try:
        methods = parse_selection_arg(args.methods, CANONICAL_METHODS, "methods")
        domains = parse_selection_arg(args.domains, CANONICAL_DOMAINS, "domains")

        if args.dry_check:
            report = dry_check(rq2_root, methods=methods, domains=domains)
            report_json = json.dumps(report, indent=2)
            print(report_json)
            if args.report_path:
                Path(args.report_path).expanduser().resolve().write_text(report_json, encoding="utf-8")
            return 0 if report["ok"] else 1

        summary = run_generation(
            rq2_root,
            settings,
            overwrite=args.overwrite,
            methods=methods,
            domains=domains,
        )
        summary_json = json.dumps(summary, indent=2)
        print(summary_json)
        if args.report_path:
            Path(args.report_path).expanduser().resolve().write_text(summary_json, encoding="utf-8")
        return 0

    except GenerationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"UNEXPECTED ERROR: {exc}", file=sys.stderr)
        return 10


if __name__ == "__main__":
    raise SystemExit(main())
