# Method Comparison: healthcare

Generated at: 2026-04-22T00:41:52

| method | micro_f1 | macro_f1 | micro_intent_completeness | macro_intent_completeness | missing | hallucinated | hallucination_rate | critical_recall | performance_range | misclassified | vague_non_resolvable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| cot | 0.556 | 0.544 | 0.660 | 0.673 | 10 | 22 | 52.4% | 0.647 | 0.214 | 8 | 17 |
| fewshot | 0.625 | 0.639 | 0.681 | 0.709 | 10 | 14 | 41.2% | 0.706 | 0.214 | 5 | 9 |
| hybrid | 0.742 | 0.748 | 0.766 | 0.771 | 7 | 9 | 28.1% | 0.765 | 0.214 | 7 | 7 |
| zeroshot | 0.528 | 0.500 | 0.660 | 0.651 | 11 | 23 | 54.8% | 0.706 | 0.214 | 9 | 17 |
