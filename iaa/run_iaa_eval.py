import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from sklearn.metrics import cohen_kappa_score


BASE_DIR = Path(__file__).resolve().parent


DATASETS = {
    "travel": {
        "human_file": "../annotations/human-annotations/annotations_travel_human.json",
        "llm_file": "../annotations/llm-annotations/annotations_travel_llm.json",
        "output_file": "reports/iaa_report_travel.json",
    },
    "healthcare": {
        "human_file": "../annotations/human-annotations/annotations_healthcare_human.json",
        "llm_file": "../annotations/llm-annotations/annotations_healthcare_llm.json",
        "output_file": "reports/iaa_report_healthcare.json",
    },
}


def load_annotations(path: str) -> dict:
    # Read one annotation JSON and index it by request_id so lookup is easy later.
    file_path = (BASE_DIR / path).resolve()
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["request_id"]: item for item in data["annotations"]}


def normalize_text(text: str, domain: str) -> str:
    # Keep normalization simple and transparent so matching is easier to explain.
    text = text.lower().strip()

    # normalize punctuation / spacing
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    text = text.replace("=", " ")
    text = text.replace(":", " ")
    text = re.sub(r"\s+", " ", text)

    # remove leading reasoning verbs for looser matching
    prefixes = [
        r"^assume\s+default\s+",
        r"^assume\s+",
        r"^resolve\s+",
        r"^ground\s+",
        r"^interpret\s+",
        r"^prefer\s+",
        r"^select\s+",
        r"^use\s+",
        r"^keep\s+",
        r"^find\s+",
        r"^plan\s+",
        r"^schedule\s+",
        r"^look\s+",
        r"^compute\s+",
        r"^treat\s+",
        r"^allow\s+",
        r"^ensure\s+",
        r"^apply\s+",
        r"^limit\s+results\s+toward\s+",
        r"^optimize\s+for\s+",
        r"^choose\s+",
        r"^coordinate\s+",
        r"^preserve\s+",
        r"^avoid\s+",
    ]
    for p in prefixes:
        text = re.sub(p, "", text)

    # lightweight lexical normalization only
    if domain == "travel":
        replacements = {
            "number of passengers": "1 passenger",
            "number of travellers": "1 passenger",
            "number of travelers": "1 passenger",
            "number of guests": "guest count",
            "number of rooms": "room count",
            "calendar date": "date",
            "current date + 1 day": "currentdate+1",
            "current date + 1": "currentdate+1",
            "frankfurt airport": "fra airport",
        }

    elif domain == "healthcare":
        replacements = {
            # temporal wording
            "calendar date": "date",
            "date grounding": "date",
            "calendar grounding": "date",
            "specific calendar date": "date",
            "concrete booking interval": "interval",
            "booking interval": "interval",
            "upcoming monday-sunday interval": "next week interval",
            "upcoming monday sunday interval": "next week interval",
            "same day": "same-day",
            "late in the afternoon": "late afternoon",
            "later in the afternoon": "late afternoon",
            "late-day": "late afternoon",
            "late day": "late afternoon",
            "current time window": "current time",

            # provider / facility wording
            "providers": "provider",
            "clinics": "clinic",
            "hospitals": "hospital",
            "facilities": "facility",
            "care setting": "facility",
            "care pathway": "pathway",
            "pathways": "pathway",
            "service area": "search area",

            # appointment / service wording
            "appointments": "appointment",
            "slots": "appointment",
            "visit composition": "visit",
            "follow-up": "follow up",
            "followup": "follow up",
            "review timing": "review date",
            "consultation pathway": "consultation route",

            # insurance / payment wording
            "public insurance": "insurance",
            "statutory insurance": "insurance",
            "gkv": "insurance",
            "tk insurance": "insurance",
            "insured with tk": "insurance",
            "covered appointment": "insurance appointment",
            "covered route": "insurance route",
            "covered providers": "insurance providers",
            "paying privately": "private pay",
            "self-pay": "private pay",
            "self pay": "private pay",
            "out-of-pocket": "insurance cost",
            "out of pocket": "insurance cost",

            # spatial wording
            "easy to reach": "accessible",
            "easy reach": "accessible",
            "nearby": "near",
            "close to": "near",
            "city-center": "central",
            "city center": "central",

            # preference / threshold wording
            "earliest possible": "earliest",
            "earliest available": "earliest",
            "as soon as possible": "earliest",
            "if clinically required": "if needed",
            "if required": "if needed",
            "if operationally possible": "if possible",
            "too long": "long",
            "waiting times": "wait time",
            "waiting time": "wait time",
            "reasonable budget": "budget",

            # morphology / spelling consistency
            "organisation": "organization",
            "prioritise": "prioritize",
            "behaviour": "behavior",
        }

    else:
        replacements = {}

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.strip()


def description_similarity(a: str, b: str, domain: str) -> float:
    # Compare normalized strings (not raw strings) to reduce wording noise.
    return SequenceMatcher(None, normalize_text(a, domain), normalize_text(b, domain)).ratio()


def greedy_align(human_constraints, llm_constraints, domain: str, threshold=0.45):
    """
    Align constraints within a request using description similarity first,
    with category as a soft preference.
    Returns:
        matched_pairs: list of (human_constraint, llm_constraint)
        unmatched_human: list
        unmatched_llm: list
    """
    used_llm = set()
    pairs = []

    # For each human constraint, pick the single best unused LLM constraint.
    for h in human_constraints:
        best_idx = None
        best_score = -1.0

        for l_idx, l in enumerate(llm_constraints):
            if l_idx in used_llm:
                continue

            sim = description_similarity(h["description"], l["description"], domain)

            # soft bonus if categories match
            if h["category"] == l["category"]:
                sim += 0.10

            if sim > best_score:
                best_score = sim
                best_idx = l_idx

        if best_idx is not None and best_score >= threshold:
            used_llm.add(best_idx)
            pairs.append((h, llm_constraints[best_idx]))

    matched_human_ids = {id(h) for h, _ in pairs}
    matched_llm_ids = {id(l) for _, l in pairs}

    unmatched_human = [h for h in human_constraints if id(h) not in matched_human_ids]
    unmatched_llm = [l for l in llm_constraints if id(l) not in matched_llm_ids]

    return pairs, unmatched_human, unmatched_llm


def density_to_label(density: str) -> str:
    return density.strip().lower()


def summarize_overlap(pairs, human_constraints, llm_constraints):
    # Basic overlap metrics used in the final report.
    if not human_constraints and not llm_constraints:
        return 1.0, 1.0, 1.0

    tp = len(pairs)
    fp = max(0, len(llm_constraints) - tp)
    fn = max(0, len(human_constraints) - tp)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def main():
    parser = argparse.ArgumentParser(description="Run IAA evaluation for a domain.")
    parser.add_argument("domain", choices=["travel", "healthcare"], help="Domain to evaluate")
    parser.add_argument(
        "--output-file",
        default=None,
        help="Optional custom output JSON path (relative to iaa/ or absolute).",
    )
    args = parser.parse_args()

    domain = args.domain.strip().lower()

    human_file = DATASETS[domain]["human_file"]
    llm_file = DATASETS[domain]["llm_file"]
    output_file = DATASETS[domain]["output_file"]
    if args.output_file:
        # Allow custom output path but keep default behavior simple.
        custom = Path(args.output_file)
        output_path = custom if custom.is_absolute() else (BASE_DIR / custom)
    else:
        output_path = BASE_DIR / output_file
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    human = load_annotations(human_file)
    llm = load_annotations(llm_file)

    common_ids = sorted(set(human.keys()) & set(llm.keys()))
    if not common_ids:
        raise ValueError("No matching request_ids found between the two files.")

    # Request-level metrics
    human_counts = []
    llm_counts = []
    human_density = []
    llm_density = []

    # Constraint-level label agreement
    cat_h, cat_l = [], []
    res_h, res_l = [], []
    imp_h, imp_l = [], []

    disagreement_report = []
    per_request_overlap = []

    for rid in common_ids:
        h_item = human[rid]
        l_item = llm[rid]

        human_counts.append(h_item["constraint_count"])
        llm_counts.append(l_item["constraint_count"])

        human_density.append(density_to_label(h_item["density"]))
        llm_density.append(density_to_label(l_item["density"]))

        h_constraints = h_item["constraints"]
        l_constraints = l_item["constraints"]

        pairs, unmatched_h, unmatched_l = greedy_align(h_constraints, l_constraints, domain)

        precision, recall, f1 = summarize_overlap(pairs, h_constraints, l_constraints)
        per_request_overlap.append({
            "request_id": rid,
            "human_count": len(h_constraints),
            "llm_count": len(l_constraints),
            "matched": len(pairs),
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
        })

        for h, l in pairs:
            cat_h.append(h["category"])
            cat_l.append(l["category"])

            res_h.append(h["resolvability"])
            res_l.append(l["resolvability"])

            imp_h.append(h["importance"])
            imp_l.append(l["importance"])

            row_diffs = {}
            for field in ["category", "resolvability", "importance"]:
                if h[field] != l[field]:
                    row_diffs[field] = {"human": h[field], "llm": l[field]}

            if row_diffs:
                disagreement_report.append({
                    "request_id": rid,
                    "human_description": h["description"],
                    "llm_description": l["description"],
                    "differences": row_diffs,
                })

        for h in unmatched_h:
            disagreement_report.append({
                "request_id": rid,
                "human_description": h["description"],
                "llm_description": None,
                "differences": {"missing_in_llm": True},
            })

        for l in unmatched_l:
            disagreement_report.append({
                "request_id": rid,
                "human_description": None,
                "llm_description": l["description"],
                "differences": {"extra_in_llm": True},
            })

    # Exact agreement on counts
    count_exact = sum(1 for a, b in zip(human_counts, llm_counts) if a == b) / len(common_ids)

    # Kappa for density
    density_kappa = cohen_kappa_score(human_density, llm_density)

    # Kappa for aligned constraints
    category_kappa = cohen_kappa_score(cat_h, cat_l) if cat_h else None
    resolvability_kappa = cohen_kappa_score(res_h, res_l) if res_h else None
    importance_kappa = cohen_kappa_score(imp_h, imp_l) if imp_h else None

    avg_precision = sum(x["precision"] for x in per_request_overlap) / len(per_request_overlap)
    avg_recall = sum(x["recall"] for x in per_request_overlap) / len(per_request_overlap)
    avg_f1 = sum(x["f1"] for x in per_request_overlap) / len(per_request_overlap)

    print(f"\n=== IAA RESULTS: {domain.upper()} ===")
    print("\n=== REQUEST-LEVEL AGREEMENT ===")
    print(f"Requests compared: {len(common_ids)}")
    print(f"Exact agreement on constraint_count: {count_exact:.3f}")
    print(f"Cohen's kappa on density: {density_kappa:.3f}")

    print("\n=== CONSTRAINT OVERLAP (description-based alignment) ===")
    print(f"Average precision: {avg_precision:.3f}")
    print(f"Average recall:    {avg_recall:.3f}")
    print(f"Average F1:        {avg_f1:.3f}")

    print("\n=== LABEL AGREEMENT ON ALIGNED CONSTRAINTS ===")
    print(f"Aligned constraint pairs: {len(cat_h)}")
    print(f"Cohen's kappa on category:      {category_kappa:.3f}" if category_kappa is not None else "No aligned pairs.")
    print(f"Cohen's kappa on resolvability: {resolvability_kappa:.3f}" if resolvability_kappa is not None else "No aligned pairs.")
    print(f"Cohen's kappa on importance:    {importance_kappa:.3f}" if importance_kappa is not None else "No aligned pairs.")

    print("\n=== PER-REQUEST OVERLAP ===")
    for row in per_request_overlap:
        print(
            f'{row["request_id"]}: '
            f'human={row["human_count"]}, llm={row["llm_count"]}, '
            f'matched={row["matched"]}, '
            f'P={row["precision"]}, R={row["recall"]}, F1={row["f1"]}'
        )

    out = {
        "domain": domain,
        "summary": {
            "requests_compared": len(common_ids),
            "constraint_count_exact_agreement": round(count_exact, 3),
            "density_kappa": round(density_kappa, 3),
            "avg_constraint_precision": round(avg_precision, 3),
            "avg_constraint_recall": round(avg_recall, 3),
            "avg_constraint_f1": round(avg_f1, 3),
            "aligned_constraint_pairs": len(cat_h),
            "category_kappa": round(category_kappa, 3) if category_kappa is not None else None,
            "resolvability_kappa": round(resolvability_kappa, 3) if resolvability_kappa is not None else None,
            "importance_kappa": round(importance_kappa, 3) if importance_kappa is not None else None,
        },
        "per_request_overlap": per_request_overlap,
        "disagreements": disagreement_report,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"\nReport written to {output_path}")

    print(f"\nSaved detailed report to {output_path}")


if __name__ == "__main__":
    main()