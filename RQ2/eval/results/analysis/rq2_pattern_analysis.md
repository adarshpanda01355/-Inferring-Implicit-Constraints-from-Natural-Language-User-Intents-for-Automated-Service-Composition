# RQ2 Pattern Analysis Summary

## Category Prevalence (Subset Overall)
- Temporal: 25 (37.88%), Spatial: 10 (15.15%), Logical: 16 (24.24%), Domain-default: 15 (22.73%)

## Per-Method Extraction Difficulty (Per Domain)
### Domain: travel

#### Method: zeroshot
#### Category-level extraction
- Temporal: gold=13, matched=7, pred=14, missed=6, over_pred=7, precision=0.500, recall=0.538, f1=0.519
- Spatial: gold=5, matched=5, pred=10, missed=0, over_pred=5, precision=0.500, recall=1.000, f1=0.667
- Logical: gold=5, matched=2, pred=10, missed=3, over_pred=8, precision=0.200, recall=0.400, f1=0.267
- Domain-default: gold=13, matched=1, pred=11, missed=12, over_pred=10, precision=0.091, recall=0.077, f1=0.083
Most difficult label (lowest recall): Domain-default (recall=0.077, matched=1/13)
Best extracted label (highest recall): Spatial (recall=1.000, matched=5/5)

#### Resolvability-level extraction
- Implicit: gold=28, matched=8, pred=30, missed=20, over_pred=22, precision=0.267, recall=0.286, f1=0.276
- Vague: gold=6, matched=1, pred=4, missed=5, over_pred=3, precision=0.250, recall=0.167, f1=0.200
- Borderline: gold=2, matched=0, pred=11, missed=2, over_pred=11, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Borderline (recall=0.000, matched=0/2)
Best extracted label (highest recall): Implicit (recall=0.286, matched=8/28)

#### Importance-level extraction
- Critical: gold=27, matched=11, pred=32, missed=16, over_pred=21, precision=0.344, recall=0.407, f1=0.373
- Useful: gold=9, matched=2, pred=13, missed=7, over_pred=11, precision=0.154, recall=0.222, f1=0.182
- Optional: gold=0, matched=0, pred=0, missed=0, over_pred=0, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Useful (recall=0.222, matched=2/9)
Best extracted label (highest recall): Critical (recall=0.407, matched=11/27)

#### Density trend: Low F1=0.397 (n=3), Medium F1=0.361 (n=4), High F1=0.338 (n=3)

#### Method: fewshot
#### Category-level extraction
- Temporal: gold=13, matched=9, pred=14, missed=4, over_pred=5, precision=0.643, recall=0.692, f1=0.667
- Spatial: gold=5, matched=5, pred=8, missed=0, over_pred=3, precision=0.625, recall=1.000, f1=0.769
- Logical: gold=5, matched=5, pred=10, missed=0, over_pred=5, precision=0.500, recall=1.000, f1=0.667
- Domain-default: gold=13, matched=8, pred=12, missed=5, over_pred=4, precision=0.667, recall=0.615, f1=0.640
Most difficult label (lowest recall): Domain-default (recall=0.615, matched=8/13)
Best extracted label (highest recall): Spatial (recall=1.000, matched=5/5)

#### Resolvability-level extraction
- Implicit: gold=28, matched=19, pred=28, missed=9, over_pred=9, precision=0.679, recall=0.679, f1=0.679
- Vague: gold=6, matched=4, pred=7, missed=2, over_pred=3, precision=0.571, recall=0.667, f1=0.615
- Borderline: gold=2, matched=1, pred=9, missed=1, over_pred=8, precision=0.111, recall=0.500, f1=0.182
Most difficult label (lowest recall): Borderline (recall=0.500, matched=1/2)
Best extracted label (highest recall): Implicit (recall=0.679, matched=19/28)

#### Importance-level extraction
- Critical: gold=27, matched=23, pred=35, missed=4, over_pred=12, precision=0.657, recall=0.852, f1=0.742
- Useful: gold=9, matched=6, pred=9, missed=3, over_pred=3, precision=0.667, recall=0.667, f1=0.667
- Optional: gold=0, matched=0, pred=0, missed=0, over_pred=0, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Useful (recall=0.667, matched=6/9)
Best extracted label (highest recall): Critical (recall=0.852, matched=23/27)

#### Density trend: Low F1=0.489 (n=3), Medium F1=0.707 (n=4), High F1=0.823 (n=3)

#### Method: cot
#### Category-level extraction
- Temporal: gold=13, matched=10, pred=17, missed=3, over_pred=7, precision=0.588, recall=0.769, f1=0.667
- Spatial: gold=5, matched=5, pred=11, missed=0, over_pred=6, precision=0.455, recall=1.000, f1=0.625
- Logical: gold=5, matched=2, pred=9, missed=3, over_pred=7, precision=0.222, recall=0.400, f1=0.286
- Domain-default: gold=13, matched=0, pred=10, missed=13, over_pred=10, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Domain-default (recall=0.000, matched=0/13)
Best extracted label (highest recall): Spatial (recall=1.000, matched=5/5)

#### Resolvability-level extraction
- Implicit: gold=28, matched=8, pred=27, missed=20, over_pred=19, precision=0.296, recall=0.286, f1=0.291
- Vague: gold=6, matched=1, pred=4, missed=5, over_pred=3, precision=0.250, recall=0.167, f1=0.200
- Borderline: gold=2, matched=1, pred=16, missed=1, over_pred=15, precision=0.062, recall=0.500, f1=0.111
Most difficult label (lowest recall): Vague (recall=0.167, matched=1/6)
Best extracted label (highest recall): Borderline (recall=0.500, matched=1/2)

#### Importance-level extraction
- Critical: gold=27, matched=12, pred=32, missed=15, over_pred=20, precision=0.375, recall=0.444, f1=0.407
- Useful: gold=9, matched=4, pred=15, missed=5, over_pred=11, precision=0.267, recall=0.444, f1=0.333
- Optional: gold=0, matched=0, pred=0, missed=0, over_pred=0, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Useful (recall=0.444, matched=4/9)
Best extracted label (highest recall): Critical (recall=0.444, matched=12/27)

#### Density trend: Low F1=0.397 (n=3), Medium F1=0.424 (n=4), High F1=0.391 (n=3)

#### Method: hybrid
#### Category-level extraction
- Temporal: gold=13, matched=10, pred=15, missed=3, over_pred=5, precision=0.667, recall=0.769, f1=0.714
- Spatial: gold=5, matched=5, pred=8, missed=0, over_pred=3, precision=0.625, recall=1.000, f1=0.769
- Logical: gold=5, matched=4, pred=8, missed=1, over_pred=4, precision=0.500, recall=0.800, f1=0.615
- Domain-default: gold=13, matched=6, pred=13, missed=7, over_pred=7, precision=0.462, recall=0.462, f1=0.462
Most difficult label (lowest recall): Domain-default (recall=0.462, matched=6/13)
Best extracted label (highest recall): Spatial (recall=1.000, matched=5/5)

#### Resolvability-level extraction
- Implicit: gold=28, matched=18, pred=31, missed=10, over_pred=13, precision=0.581, recall=0.643, f1=0.610
- Vague: gold=6, matched=4, pred=5, missed=2, over_pred=1, precision=0.800, recall=0.667, f1=0.727
- Borderline: gold=2, matched=0, pred=8, missed=2, over_pred=8, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Borderline (recall=0.000, matched=0/2)
Best extracted label (highest recall): Vague (recall=0.667, matched=4/6)

#### Importance-level extraction
- Critical: gold=27, matched=20, pred=37, missed=7, over_pred=17, precision=0.541, recall=0.741, f1=0.625
- Useful: gold=9, matched=5, pred=7, missed=4, over_pred=2, precision=0.714, recall=0.556, f1=0.625
- Optional: gold=0, matched=0, pred=0, missed=0, over_pred=0, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Useful (recall=0.556, matched=5/9)
Best extracted label (highest recall): Critical (recall=0.741, matched=20/27)

#### Density trend: Low F1=0.495 (n=3), Medium F1=0.598 (n=4), High F1=0.790 (n=3)

### Domain: healthcare

#### Method: zeroshot
#### Category-level extraction
- Temporal: gold=12, matched=8, pred=10, missed=4, over_pred=2, precision=0.800, recall=0.667, f1=0.727
- Spatial: gold=5, matched=3, pred=6, missed=2, over_pred=3, precision=0.500, recall=0.600, f1=0.545
- Logical: gold=11, matched=5, pred=12, missed=6, over_pred=7, precision=0.417, recall=0.455, f1=0.435
- Domain-default: gold=2, matched=0, pred=14, missed=2, over_pred=14, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Domain-default (recall=0.000, matched=0/2)
Best extracted label (highest recall): Temporal (recall=0.667, matched=8/12)

#### Resolvability-level extraction
- Implicit: gold=25, matched=12, pred=26, missed=13, over_pred=14, precision=0.462, recall=0.480, f1=0.471
- Vague: gold=2, matched=1, pred=2, missed=1, over_pred=1, precision=0.500, recall=0.500, f1=0.500
- Borderline: gold=3, matched=2, pred=14, missed=1, over_pred=12, precision=0.143, recall=0.667, f1=0.235
Most difficult label (lowest recall): Implicit (recall=0.480, matched=12/25)
Best extracted label (highest recall): Borderline (recall=0.667, matched=2/3)

#### Importance-level extraction
- Critical: gold=17, matched=11, pred=28, missed=6, over_pred=17, precision=0.393, recall=0.647, f1=0.489
- Useful: gold=13, matched=4, pred=14, missed=9, over_pred=10, precision=0.286, recall=0.308, f1=0.296
- Optional: gold=0, matched=0, pred=0, missed=0, over_pred=0, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Useful (recall=0.308, matched=4/13)
Best extracted label (highest recall): Critical (recall=0.647, matched=11/17)

#### Density trend: Low F1=0.408 (n=5), Medium F1=0.607 (n=3), High F1=0.573 (n=2)

#### Method: fewshot
#### Category-level extraction
- Temporal: gold=12, matched=9, pred=11, missed=3, over_pred=2, precision=0.818, recall=0.750, f1=0.783
- Spatial: gold=5, matched=3, pred=3, missed=2, over_pred=0, precision=1.000, recall=0.600, f1=0.750
- Logical: gold=11, matched=8, pred=17, missed=3, over_pred=9, precision=0.471, recall=0.727, f1=0.571
- Domain-default: gold=2, matched=0, pred=3, missed=2, over_pred=3, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Domain-default (recall=0.000, matched=0/2)
Best extracted label (highest recall): Temporal (recall=0.750, matched=9/12)

#### Resolvability-level extraction
- Implicit: gold=25, matched=15, pred=26, missed=10, over_pred=11, precision=0.577, recall=0.600, f1=0.588
- Vague: gold=2, matched=2, pred=5, missed=0, over_pred=3, precision=0.400, recall=1.000, f1=0.571
- Borderline: gold=3, matched=1, pred=3, missed=2, over_pred=2, precision=0.333, recall=0.333, f1=0.333
Most difficult label (lowest recall): Borderline (recall=0.333, matched=1/3)
Best extracted label (highest recall): Vague (recall=1.000, matched=2/2)

#### Importance-level extraction
- Critical: gold=17, matched=12, pred=24, missed=5, over_pred=12, precision=0.500, recall=0.706, f1=0.585
- Useful: gold=13, matched=5, pred=10, missed=8, over_pred=5, precision=0.500, recall=0.385, f1=0.435
- Optional: gold=0, matched=0, pred=0, missed=0, over_pred=0, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Useful (recall=0.385, matched=5/13)
Best extracted label (highest recall): Critical (recall=0.706, matched=12/17)

#### Density trend: Low F1=0.640 (n=5), Medium F1=0.694 (n=3), High F1=0.556 (n=2)

#### Method: cot
#### Category-level extraction
- Temporal: gold=12, matched=9, pred=11, missed=3, over_pred=2, precision=0.818, recall=0.750, f1=0.783
- Spatial: gold=5, matched=3, pred=5, missed=2, over_pred=2, precision=0.600, recall=0.600, f1=0.600
- Logical: gold=11, matched=6, pred=13, missed=5, over_pred=7, precision=0.462, recall=0.545, f1=0.500
- Domain-default: gold=2, matched=1, pred=13, missed=1, over_pred=12, precision=0.077, recall=0.500, f1=0.133
Most difficult label (lowest recall): Domain-default (recall=0.500, matched=1/2)
Best extracted label (highest recall): Temporal (recall=0.750, matched=9/12)

#### Resolvability-level extraction
- Implicit: gold=25, matched=10, pred=25, missed=15, over_pred=15, precision=0.400, recall=0.400, f1=0.400
- Vague: gold=2, matched=0, pred=3, missed=2, over_pred=3, precision=0.000, recall=0.000, f1=0.000
- Borderline: gold=3, matched=3, pred=14, missed=0, over_pred=11, precision=0.214, recall=1.000, f1=0.353
Most difficult label (lowest recall): Vague (recall=0.000, matched=0/2)
Best extracted label (highest recall): Borderline (recall=1.000, matched=3/3)

#### Importance-level extraction
- Critical: gold=17, matched=11, pred=29, missed=6, over_pred=18, precision=0.379, recall=0.647, f1=0.478
- Useful: gold=13, matched=8, pred=13, missed=5, over_pred=5, precision=0.615, recall=0.615, f1=0.615
- Optional: gold=0, matched=0, pred=0, missed=0, over_pred=0, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Useful (recall=0.615, matched=8/13)
Best extracted label (highest recall): Critical (recall=0.647, matched=11/17)

#### Density trend: Low F1=0.484 (n=5), Medium F1=0.607 (n=3), High F1=0.600 (n=2)

#### Method: hybrid
#### Category-level extraction
- Temporal: gold=12, matched=9, pred=11, missed=3, over_pred=2, precision=0.818, recall=0.750, f1=0.783
- Spatial: gold=5, matched=4, pred=4, missed=1, over_pred=0, precision=1.000, recall=0.800, f1=0.889
- Logical: gold=11, matched=9, pred=16, missed=2, over_pred=7, precision=0.562, recall=0.818, f1=0.667
- Domain-default: gold=2, matched=0, pred=1, missed=2, over_pred=1, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Domain-default (recall=0.000, matched=0/2)
Best extracted label (highest recall): Logical (recall=0.818, matched=9/11)

#### Resolvability-level extraction
- Implicit: gold=25, matched=18, pred=25, missed=7, over_pred=7, precision=0.720, recall=0.720, f1=0.720
- Vague: gold=2, matched=2, pred=5, missed=0, over_pred=3, precision=0.400, recall=1.000, f1=0.571
- Borderline: gold=3, matched=1, pred=2, missed=2, over_pred=1, precision=0.500, recall=0.333, f1=0.400
Most difficult label (lowest recall): Borderline (recall=0.333, matched=1/3)
Best extracted label (highest recall): Vague (recall=1.000, matched=2/2)

#### Importance-level extraction
- Critical: gold=17, matched=13, pred=22, missed=4, over_pred=9, precision=0.591, recall=0.765, f1=0.667
- Useful: gold=13, matched=6, pred=10, missed=7, over_pred=4, precision=0.600, recall=0.462, f1=0.522
- Optional: gold=0, matched=0, pred=0, missed=0, over_pred=0, precision=0.000, recall=0.000, f1=0.000
Most difficult label (lowest recall): Useful (recall=0.462, matched=6/13)
Best extracted label (highest recall): Critical (recall=0.765, matched=13/17)

#### Density trend: Low F1=0.720 (n=5), Medium F1=0.774 (n=3), High F1=0.778 (n=2)

## Cross-Domain Synthesis

| Method | T-F1 | H-F1 | T-IC | H-IC | Avg-F1 | Avg-IC |
|---|---:|---:|---:|---:|---:|---:|
| hybrid | 0.650 | 0.742 | 0.730 | 0.766 | 0.696 | 0.748 |
| fewshot | 0.725 | 0.625 | 0.825 | 0.681 | 0.675 | 0.753 |
| cot | 0.410 | 0.556 | 0.460 | 0.660 | 0.483 | 0.560 |
| zeroshot | 0.370 | 0.528 | 0.429 | 0.660 | 0.449 | 0.544 |

Best Avg-F1 method: hybrid (0.696) | Best Avg-IC method: fewshot (0.753)
Travel F1 range: 0.355 | Healthcare F1 range: 0.214

