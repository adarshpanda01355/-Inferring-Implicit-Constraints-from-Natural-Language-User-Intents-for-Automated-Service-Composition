# RQ2 Evaluation Summary: healthcare / fewshot

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
- Prediction folder: C:\Users\adars\Desktop\ResearchProjectCodeBase\RQ2\fewshot\llm_outputs\healthcare

## Run Counts
- Subset requests loaded: 10
- Gold requests loaded: 25
- Prediction files found: 10
- Total aligned pairs: 20

## Aggregate Metrics
- Micro extraction: precision=0.588, recall=0.667, f1=0.625
- Macro extraction: precision=0.608, recall=0.708, f1=0.639
- Intent completeness: micro=0.681, macro=0.709
- Label agreement (micro): category=1.000, resolvability=0.900, importance=0.850
- Error taxonomy totals: missing=10, hallucinated=14, hallucination_rate=41.2%, critical_recall=0.706, performance_range=0.000, misclassified=5, vague_non_resolvable=9

## Per-Request Table
| request_id | gold | pred | matched | precision | recall | f1 | intent_completeness | missing | hallucinated | misclassified | vague_non_resolvable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| HEALTH_001 | 2 | 4 | 2 | 0.500 | 1.000 | 0.667 | 1.000 | 0 | 2 | 0 | 1 |
| HEALTH_007 | 2 | 3 | 2 | 0.667 | 1.000 | 0.800 | 1.000 | 0 | 1 | 0 | 1 |
| HEALTH_023 | 5 | 4 | 2 | 0.500 | 0.400 | 0.444 | 0.375 | 3 | 2 | 1 | 1 |
| HEALTH_002 | 2 | 4 | 1 | 0.250 | 0.500 | 0.333 | 0.333 | 1 | 3 | 1 | 2 |
| HEALTH_010 | 3 | 3 | 2 | 0.667 | 0.667 | 0.667 | 0.750 | 1 | 1 | 0 | 0 |
| HEALTH_011 | 4 | 4 | 3 | 0.750 | 0.750 | 0.750 | 0.667 | 1 | 1 | 1 | 1 |
| HEALTH_018 | 5 | 4 | 3 | 0.750 | 0.600 | 0.667 | 0.714 | 2 | 1 | 1 | 2 |
| HEALTH_005 | 2 | 2 | 2 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | 0 | 0 | 0 |
| HEALTH_006 | 2 | 3 | 1 | 0.333 | 0.500 | 0.400 | 0.500 | 1 | 2 | 0 | 1 |
| HEALTH_016 | 3 | 3 | 2 | 0.667 | 0.667 | 0.667 | 0.750 | 1 | 1 | 1 | 0 |
