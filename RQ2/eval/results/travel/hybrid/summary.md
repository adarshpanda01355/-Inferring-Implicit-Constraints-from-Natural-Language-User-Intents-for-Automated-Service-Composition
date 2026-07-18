# RQ2 Evaluation Summary: travel / hybrid

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
- Prediction folder: C:\Users\adars\Desktop\ResearchProjectCodeBase\RQ2\hybrid\llm_outputs\travel

## Run Counts
- Subset requests loaded: 10
- Gold requests loaded: 25
- Prediction files found: 10
- Total aligned pairs: 26

## Aggregate Metrics
- Micro extraction: precision=0.591, recall=0.722, f1=0.650
- Macro extraction: precision=0.576, recall=0.717, f1=0.625
- Intent completeness: micro=0.730, macro=0.731
- Label agreement (micro): category=0.962, resolvability=0.846, importance=0.962
- Error taxonomy totals: missing=10, hallucinated=18, hallucination_rate=40.9%, critical_recall=0.741, performance_range=0.000, misclassified=5, vague_non_resolvable=13

## Per-Request Table
| request_id | gold | pred | matched | precision | recall | f1 | intent_completeness | missing | hallucinated | misclassified | vague_non_resolvable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TRAVEL_001 | 2 | 3 | 1 | 0.333 | 0.500 | 0.400 | 0.500 | 1 | 2 | 0 | 0 |
| TRAVEL_002 | 4 | 4 | 2 | 0.500 | 0.500 | 0.500 | 0.429 | 2 | 2 | 0 | 1 |
| TRAVEL_005 | 6 | 4 | 3 | 0.750 | 0.500 | 0.600 | 0.545 | 3 | 1 | 0 | 1 |
| TRAVEL_006 | 5 | 5 | 5 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 | 0 | 1 |
| TRAVEL_007 | 2 | 3 | 2 | 0.667 | 1.000 | 0.800 | 1.000 | 0 | 1 | 0 | 0 |
| TRAVEL_010 | 3 | 4 | 2 | 0.500 | 0.667 | 0.571 | 0.750 | 1 | 2 | 0 | 2 |
| TRAVEL_011 | 3 | 4 | 2 | 0.500 | 0.667 | 0.571 | 0.600 | 1 | 2 | 1 | 1 |
| TRAVEL_016 | 6 | 7 | 5 | 0.714 | 0.833 | 0.769 | 0.818 | 1 | 2 | 2 | 3 |
| TRAVEL_018 | 3 | 5 | 3 | 0.600 | 1.000 | 0.750 | 1.000 | 0 | 2 | 1 | 1 |
| TRAVEL_023 | 2 | 5 | 1 | 0.200 | 0.500 | 0.286 | 0.667 | 1 | 4 | 1 | 3 |
