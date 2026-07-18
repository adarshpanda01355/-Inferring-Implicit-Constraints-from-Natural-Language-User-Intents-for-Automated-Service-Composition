# RQ2 Evaluation Summary: travel / cot

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
- Gold file: C:\Users\adars\Desktop\ResearchProjectCodeBase\RQ2\data\annotations_travel_gold.json
- Subset file: C:\Users\adars\Desktop\ResearchProjectCodeBase\RQ2\data\travelrequests_subset.json
- Prediction folder: C:\Users\adars\Desktop\ResearchProjectCodeBase\RQ2\cot\llm_outputs\travel

## Run Counts
- Subset requests loaded: 10
- Gold requests loaded: 25
- Prediction files found: 10
- Total aligned pairs: 17

## Aggregate Metrics
- Micro extraction: precision=0.362, recall=0.472, f1=0.410
- Macro extraction: precision=0.355, recall=0.523, f1=0.406
- Intent completeness: micro=0.460, macro=0.531
- Label agreement (micro): category=1.000, resolvability=0.588, importance=0.941
- Error taxonomy totals: missing=19, hallucinated=30, hallucination_rate=63.8%, critical_recall=0.444, performance_range=0.000, misclassified=7, vague_non_resolvable=20

## Per-Request Table
| request_id | gold | pred | matched | precision | recall | f1 | intent_completeness | missing | hallucinated | misclassified | vague_non_resolvable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TRAVEL_001 | 2 | 5 | 1 | 0.200 | 0.500 | 0.286 | 0.500 | 1 | 4 | 0 | 1 |
| TRAVEL_002 | 4 | 5 | 2 | 0.400 | 0.500 | 0.444 | 0.429 | 2 | 3 | 1 | 2 |
| TRAVEL_005 | 6 | 5 | 2 | 0.400 | 0.333 | 0.364 | 0.364 | 4 | 3 | 0 | 1 |
| TRAVEL_006 | 5 | 4 | 2 | 0.500 | 0.400 | 0.444 | 0.400 | 3 | 2 | 2 | 2 |
| TRAVEL_007 | 2 | 4 | 1 | 0.250 | 0.500 | 0.333 | 0.500 | 1 | 3 | 0 | 3 |
| TRAVEL_010 | 3 | 5 | 2 | 0.400 | 0.667 | 0.500 | 0.750 | 1 | 3 | 0 | 3 |
| TRAVEL_011 | 3 | 4 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 3 | 4 | 0 | 1 |
| TRAVEL_016 | 6 | 5 | 2 | 0.400 | 0.333 | 0.364 | 0.364 | 4 | 3 | 1 | 3 |
| TRAVEL_018 | 3 | 5 | 3 | 0.600 | 1.000 | 0.750 | 1.000 | 0 | 2 | 3 | 3 |
| TRAVEL_023 | 2 | 5 | 2 | 0.400 | 1.000 | 0.571 | 1.000 | 0 | 3 | 0 | 1 |
