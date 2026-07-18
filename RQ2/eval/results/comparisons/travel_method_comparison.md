# Method Comparison: travel

Generated at: 2026-04-22T00:41:52

| method | micro_f1 | macro_f1 | micro_intent_completeness | macro_intent_completeness | missing | hallucinated | hallucination_rate | critical_recall | performance_range | misclassified | vague_non_resolvable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cot | 0.410 | 0.406 | 0.460 | 0.531 | 19 | 30 | 63.8% | 0.444 | 0.355 | 7 | 20 |
| fewshot | 0.725 | 0.676 | 0.825 | 0.811 | 7 | 15 | 34.1% | 0.852 | 0.355 | 7 | 16 |
| hybrid | 0.650 | 0.625 | 0.730 | 0.731 | 10 | 18 | 40.9% | 0.741 | 0.355 | 5 | 13 |
| zeroshot | 0.370 | 0.365 | 0.429 | 0.502 | 21 | 30 | 66.7% | 0.444 | 0.355 | 7 | 15 |
