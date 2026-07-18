# IAA Module (Inter-Annotator Agreement)

This folder contains the script used to measure agreement between human annotations and LLM annotations.

## What this script does

The script compares annotations request by request and reports:

- request-level agreement (constraint counts and density)
- overlap quality between human and LLM constraints (Precision, Recall, F1)
- label agreement on aligned constraints (Category, Resolvability, Importance) using Cohen's kappa
- detailed disagreement list for manual review

Main script:

- [run_iaa_eval.py](run_iaa_eval.py)

## Input files

The script reads these files:

- [../annotations/human-annotations/annotations_travel_human.json](../annotations/human-annotations/annotations_travel_human.json)
- [../annotations/llm-annotations/annotations_travel_llm.json](../annotations/llm-annotations/annotations_travel_llm.json)
- [../annotations/human-annotations/annotations_healthcare_human.json](../annotations/human-annotations/annotations_healthcare_human.json)
- [../annotations/llm-annotations/annotations_healthcare_llm.json](../annotations/llm-annotations/annotations_healthcare_llm.json)

## Output files

Default outputs are written to:

- [reports/iaa_report_travel.json](reports/iaa_report_travel.json)
- [reports/iaa_report_healthcare.json](reports/iaa_report_healthcare.json)

## How to run

Run from project root:

```bash
python iaa/run_iaa_eval.py travel
python iaa/run_iaa_eval.py healthcare
```

Optional custom output path:

```bash
python iaa/run_iaa_eval.py healthcare --output-file reports/iaa_report_healthcare_test.json
```

This means: save the result to a different file name/path instead of the default healthcare report file.
- If you run without `--output-file`, it writes to the default file and replaces that file.
- If you want to keep old results, run with `--output-file` and a different name.

## Run modes

The script supports two evaluation modes by domain:

- `travel`
- `healthcare`

## How to read the generated report

Each output JSON has three main parts:

1. `summary`: overall agreement numbers for the domain (count agreement, density kappa, average precision/recall/F1, and kappa for labels).
2. `per_request_overlap`: request-by-request matching quality (how many constraints matched, plus P/R/F1 for each request ID).
3. `disagreements`: detailed mismatch records for manual inspection (label mismatches, missing constraints, and extra constraints).

Quick reading order:

1. Check `summary` first for the big picture.
2. Check `per_request_overlap` to find weak requests.
3. Use `disagreements` to understand exactly what went wrong.

## Small technical implementation note

The implementation uses these steps:

1. Load human and LLM annotations for the selected domain.
2. Normalize text (lowercase, punctuation cleanup, and small domain-specific term normalization).
3. Align constraints using greedy matching with description similarity.
4. Add a small soft bonus when categories match.
5. Compute overlap metrics and agreement metrics.
6. Save summary + per-request overlap + disagreement details to JSON.

Important matching settings in the script:

- description alignment threshold: `0.45`
- category soft bonus during alignment: `+0.10`

## Dependencies

Required Python packages:

- `scikit-learn` (for Cohen's kappa)

If needed:

```bash
pip install scikit-learn
```
