# RQ2 Evaluation Summary: healthcare / zeroshot

Generated at: 2026-04-22T00:41:52

## Evaluator Configuration
- match_threshold: 0.25
- category_bonus: 0.05
- hybrid_source: validator
- allow_subset_fallback: False
- warnings_as_errors: False
- require_complete_predictions: False

## Folder Conventions
- Canonical methods: zeroshot, fewshot, cot, hybrid
- Default prediction path pattern: <method>/llm_outputs/<domain>
- Hybrid preferred path: hybrid/validator_outputs/<domain> (fallback to llm_outputs)

## Data And Paths
- Gold file: C:\Users\adars\Desktop\ResearchProjectCodeBase\RQ2\data\annotations_healthcare_gold.json
- Subset file: C:\Users\adars\Desktop\ResearchProjectCodeBase\RQ2\data\healthcarerequests_subset.json
- Prediction folder: C:\Users\adars\Desktop\ResearchProjectCodeBase\RQ2\zeroshot\llm_outputs\healthcare

## Run Counts
- Subset requests loaded: 10
- Gold requests loaded: 25
- Prediction files found: 10
- Total aligned pairs: 19

## Aggregate Metrics
- Micro extraction: precision=0.452, recall=0.633, f1=0.528
- Macro extraction: precision=0.432, recall=0.628, f1=0.500
- Intent completeness: micro=0.660, macro=0.651
- Label agreement (micro): category=0.842, resolvability=0.789, importance=0.789
- Error taxonomy totals: missing=11, hallucinated=23, hallucination_rate=54.8%, critical_recall=0.706, performance_range=0.000, misclassified=9, vague_non_resolvable=17

## Per-Request Table
| request_id | gold | pred | matched | precision | recall | f1 | intent_completeness | missing | hallucinated | misclassified | vague_non_resolvable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HEALTH_001 | 2 | 5 | 2 | 0.400 | 1.000 | 0.571 | 1.000 | 0 | 3 | 1 | 2 |
| HEALTH_007 | 2 | 4 | 2 | 0.500 | 1.000 | 0.667 | 1.000 | 0 | 2 | 1 | 2 |
| HEALTH_023 | 5 | 6 | 3 | 0.500 | 0.600 | 0.545 | 0.625 | 2 | 3 | 1 | 2 |
| HEALTH_002 | 2 | 3 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 2 | 3 | 0 | 2 |
| HEALTH_010 | 3 | 5 | 2 | 0.400 | 0.667 | 0.500 | 0.750 | 1 | 3 | 1 | 2 |
| HEALTH_011 | 4 | 4 | 3 | 0.750 | 0.750 | 0.750 | 0.667 | 1 | 1 | 1 | 2 |
| HEALTH_018 | 5 | 5 | 3 | 0.600 | 0.600 | 0.600 | 0.714 | 2 | 2 | 2 | 3 |
| HEALTH_005 | 2 | 3 | 1 | 0.333 | 0.500 | 0.400 | 0.500 | 1 | 2 | 0 | 0 |
| HEALTH_006 | 2 | 3 | 1 | 0.333 | 0.500 | 0.400 | 0.500 | 1 | 2 | 1 | 2 |
| HEALTH_016 | 3 | 4 | 2 | 0.500 | 0.667 | 0.571 | 0.750 | 1 | 2 | 1 | 0 |
