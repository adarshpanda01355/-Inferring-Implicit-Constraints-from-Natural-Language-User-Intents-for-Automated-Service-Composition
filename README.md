# Supplementary Material
The supplementary material accompanying this paper is available in this repository and can be accessed directly here:
https://anonymous.4open.science/r/IICNLUSIASC-72FE/ICSOC_2026_Supplementary_Material.pdf
This document contains additional implementation details, prompts, datasets, evaluation results, and supporting information that complement the paper.

# Codebase
This repository contains the code and outputs used in the paper.

## Main folders

- [iaa](iaa): Inter-Annotator Agreement script and reports
- [RQ2/generation](RQ2/generation): LLM output generation script and run summaries
- [RQ2/eval](RQ2/eval): evaluation and pattern analysis scripts + results
- [annotations](annotations): annotation files (gold, human, llm)
- [RQ2/data](RQ2/data): fixed RQ2 gold/subset input files

## Folder structure (brief)

- [annotations](annotations)
  - [annotations/gold-annotations](annotations/gold-annotations): finalized gold annotation files
  - [annotations/human-annotations](annotations/human-annotations): human annotation files
  - [annotations/llm-annotations](annotations/llm-annotations): LLM annotation files

- [iaa](iaa)
  - [iaa/run_iaa_eval.py](iaa/run_iaa_eval.py): computes IAA metrics
  - [iaa/reports](iaa/reports): final IAA JSON reports

- [RQ2](RQ2)
  - [RQ2/data](RQ2/data): RQ2 evaluation gold and subset snapshots
  - [RQ2/zeroshot](RQ2/zeroshot), [RQ2/fewshot](RQ2/fewshot), [RQ2/cot](RQ2/cot), [RQ2/hybrid](RQ2/hybrid)
    - each folder contains prompt file + `llm_outputs` + `llm_raw_failures`
  - [RQ2/generation](RQ2/generation)
    - [RQ2/generation/generate_llm_outputs.py](RQ2/generation/generate_llm_outputs.py)
    - [RQ2/generation/reports](RQ2/generation/reports): generation summary snapshots
  - [RQ2/eval](RQ2/eval)
    - [RQ2/eval/evaluate_rq2.py](RQ2/eval/evaluate_rq2.py)
    - [RQ2/eval/analyze_rq2_patterns.py](RQ2/eval/analyze_rq2_patterns.py)
    - [RQ2/eval/generate_figures.py](RQ2/eval/generate_figures.py)
    - [RQ2/eval/results](RQ2/eval/results): evaluation and analysis artifacts

## Workflow overview

Project sequence used in this work (brief):

1. Dataset design and subset setup:
  `domain requests` -> `annotation-ready dataset` + `RQ2 subset design`
2. Dual annotation:
  `dataset` -> `human annotations` + `LLM annotations`
3. IAA quality check and adjudication:
  `human + LLM annotations` -> `iaa/run_iaa_eval.py` -> `iaa/reports` -> `adjudication`
4. Gold finalization and freeze:
  `adjudicated annotations` -> `gold annotations` -> `RQ2/data` snapshot
5. Generate method outputs:
  `RQ2/generation/generate_llm_outputs.py` -> `zeroshot/fewshot/cot/hybrid llm_outputs`
6. Evaluate method performance:
  `RQ2/eval/evaluate_rq2.py` -> `RQ2/eval/results` (metrics + summaries)
7. Run consolidated analysis:
  `RQ2/eval/analyze_rq2_patterns.py` -> `RQ2/eval/results/analysis`

## Quick setup

1. Install Python (recommended: 3.10+)
2. Install dependencies:

```bash
pip install -r requirements.txt
```

This also installs plotting dependencies used by [RQ2/eval/generate_figures.py](RQ2/eval/generate_figures.py).

3. Set OpenAI API key (required only for generation):

```powershell
setx OPENAI_API_KEY "YOUR_API_KEY_HERE"
```

Open a new terminal after running `setx`.

## Quick run commands

### IAA

```bash
python iaa/run_iaa_eval.py travel
python iaa/run_iaa_eval.py healthcare
```

### RQ2 generation (dry check)

```bash
python RQ2/generation/generate_llm_outputs.py --dry-check --methods all --domains all
```

### RQ2 evaluation

```bash
python RQ2/eval/evaluate_rq2.py --domain all --method all --match-threshold 0.25 --category-bonus 0.05 --hybrid-source validator
python RQ2/eval/analyze_rq2_patterns.py --match-threshold 0.25 --category-bonus 0.05 --hybrid-source validator
python RQ2/eval/generate_figures.py
```

## Notes

- Full output artifacts are included in this codebase.
- For detailed usage, see module READMEs:
  - [iaa/readme.md](iaa/readme.md)
  - [RQ2/generation/readme.md](RQ2/generation/readme.md)
  - [RQ2/eval/readme.md](RQ2/eval/readme.md)
