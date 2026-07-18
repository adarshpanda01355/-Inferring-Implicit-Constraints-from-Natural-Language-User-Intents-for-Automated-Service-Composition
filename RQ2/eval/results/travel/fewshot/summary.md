# RQ2 Evaluation Summary: travel / fewshot

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
- Prediction folder: C:\Users\adars\Desktop\ResearchProjectCodeBase\RQ2\fewshot\llm_outputs\travel

## Run Counts
- Subset requests loaded: 10
- Gold requests loaded: 25
- Prediction files found: 10
- Total aligned pairs: 29

## Aggregate Metrics
- Micro extraction: precision=0.659, recall=0.806, f1=0.725
- Macro extraction: precision=0.611, recall=0.783, f1=0.676
- Intent completeness: micro=0.825, macro=0.811
- Label agreement (micro): category=0.931, resolvability=0.828, importance=1.000
- Error taxonomy totals: missing=7, hallucinated=15, hallucination_rate=34.1%, critical_recall=0.852, performance_range=0.000, misclassified=7, vague_non_resolvable=16

## Per-Request Table
| request_id | gold | pred | matched | precision | recall | f1 | intent_completeness | missing | hallucinated | misclassified | vague_non_resolvable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TRAVEL_001 | 2 | 3 | 1 | 0.333 | 0.500 | 0.400 | 0.500 | 1 | 2 | 0 | 0 |
| TRAVEL_002 | 4 | 5 | 4 | 0.800 | 1.000 | 0.889 | 1.000 | 0 | 1 | 0 | 2 |
| TRAVEL_005 | 6 | 5 | 3 | 0.600 | 0.500 | 0.545 | 0.545 | 3 | 2 | 1 | 1 |
| TRAVEL_006 | 5 | 5 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 | 0 | 1 |
| TRAVEL_007 | 2 | 4 | 2 | 0.500 | 1.000 | 0.667 | 1.000 | 0 | 2 | 0 | 0 |
| TRAVEL_010 | 3 | 4 | 3 | 0.750 | 1.000 | 0.857 | 1.000 | 0 | 1 | 0 | 2 |
| TRAVEL_011 | 3 | 3 | 1 | 0.333 | 0.333 | 0.333 | 0.400 | 2 | 2 | 0 | 1 |
| TRAVEL_016 | 6 | 7 | 6 | 0.857 | 1.000 | 0.923 | 1.000 | 0 | 1 | 3 | 3 |
| TRAVEL_018 | 3 | 5 | 3 | 0.600 | 1.000 | 0.750 | 1.000 | 0 | 2 | 2 | 3 |
| TRAVEL_023 | 2 | 3 | 1 | 0.333 | 0.500 | 0.400 | 0.667 | 1 | 2 | 1 | 3 |
