# RQ2 Evaluation Module

This folder contains the scripts used to evaluate and analyze RQ2 outputs.

## What these scripts do

This module has three scripts:

- [evaluate_rq2.py](evaluate_rq2.py): runs core evaluation (matching, metrics, errors, summaries)
- [analyze_rq2_patterns.py](analyze_rq2_patterns.py): runs consolidated pattern analysis across labels and density
- [generate_figures.py](generate_figures.py): generates thesis figures from evaluation and gold annotation outputs

Together they produce the final RQ2 evaluation artifacts and figure outputs.

## Input files

The evaluator reads inputs from the RQ2 root:

- gold annotations snapshot from [../data](../data)
- fixed subset files from [../data](../data)
- model outputs from:
  - [../zeroshot/llm_outputs](../zeroshot/llm_outputs)
  - [../fewshot/llm_outputs](../fewshot/llm_outputs)
  - [../cot/llm_outputs](../cot/llm_outputs)
  - [../hybrid/llm_outputs](../hybrid/llm_outputs)

## Output files

Main outputs are written to:

- [results](results)
- [results/comparisons](results/comparisons)
- [results/analysis](results/analysis)
- [results/travel](results/travel)
- [results/healthcare](results/healthcare)
- [results/figures](results/figures)

## Prerequisites

Before running:

- Python installed
- RQ2 generation outputs already available in method output folders
- dependencies installed from [../../requirements.txt](../../requirements.txt)

This evaluation module uses Python dependencies listed in [../../requirements.txt](../../requirements.txt).

## How to run

Run from project root.

Core evaluator (all domains and methods):

```bash
python RQ2/eval/evaluate_rq2.py --domain all --method all --match-threshold 0.25 --category-bonus 0.05 --hybrid-source validator
```

Consolidated pattern analysis (same settings):

```bash
python RQ2/eval/analyze_rq2_patterns.py --match-threshold 0.25 --category-bonus 0.05 --hybrid-source validator
```

Figure generation:

```bash
python RQ2/eval/generate_figures.py
```

Optional examples:

```bash
python RQ2/eval/evaluate_rq2.py --domain travel --method fewshot --match-threshold 0.25 --category-bonus 0.05 --hybrid-source validator
python RQ2/eval/evaluate_rq2.py --domain all --method all --warnings-as-errors --require-complete-predictions
```

## Run modes

### evaluate_rq2.py

Supports:

- domains: `travel`, `healthcare`, `all`
- methods: `zeroshot`, `fewshot`, `cot`, `hybrid`, `all`
- configurable matching settings (`--match-threshold`, `--category-bonus`)
- acceptance policy flags (`--warnings-as-errors`, `--require-complete-predictions`)

### analyze_rq2_patterns.py

Supports:

- consolidated pattern analysis for all methods/domains
- same matching settings as evaluator for consistency

### generate_figures.py

Supports:

- figure generation from evaluation comparison JSONs and gold annotations
- writing PDF figures to [results/figures](results/figures)

## How to read the generated outputs (brief)

Quick reading order:

1. Start with run summaries in [results](results) for high-level metrics.
2. Check [results/comparisons](results/comparisons) for cross-method comparison per domain.
3. Check [results/analysis](results/analysis) for category/resolvability/importance/density patterns.
4. Use per-request outputs under domain/method folders when detailed debugging is needed.

## Small technical implementation note

### evaluate_rq2.py logic

1. Load gold/subset/prediction files.
2. Validate prediction JSON schema.
3. Normalize constraint text and align predictions to gold constraints using deterministic greedy matching.
4. Compute micro/macro metrics, intent completeness, label accuracies, and error counts.
5. Write JSON/CSV/Markdown artifacts into the results tree.

### analyze_rq2_patterns.py logic

1. Reuse evaluator alignment logic.
2. Aggregate performance by category, resolvability, importance, and density.
3. Export consolidated CSV and markdown reports for interpretation.

### generate_figures.py logic

1. Load domain comparison JSON files from [results/comparisons](results/comparisons).
2. Load gold annotations and compute category distribution percentages.
3. Build three matplotlib figures: method comparison, category distribution, and hallucination rate.
4. Save PDF outputs into [results/figures](results/figures).
