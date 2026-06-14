# AML Detection System Scorecard

## Overall Performance Lift (Rules vs Ensemble)
*Operating Point: Score >= 50*

| Metric | Rules Only (v2-v4) | Rules + ML Ensemble (v5) | Lift |
|--------|-------------------|--------------------------|------|
| **Recall** | 50.0% | 59.6% | **+9.6%** |
| **Precision** | 85.6% | 85.5% | -0.1% |
| **FPR** | 1.92% | 2.31% | +0.38% |
| **F1 Score** | 0.631 | 0.702 | +0.071 |
| **PR-AUC** | 0.729 | 0.802 | +0.073 |

## Detection Rate by Anomaly Type

| Anomaly Type | Rules Only | Rules + ML |
|--------------|------------|------------|
| none | 0.0% | 0.0% |
| structuring | 100.0% | 100.0% |
| velocity_fraud | 21.9% | 36.8% |
| large_amount | 100.0% | 100.0% |
| geo_anomaly | 100.0% | 100.0% |

    
## Context
- **Dataset**: Synthetic local generation (v1 schema)
- **Class Imbalance**: ~5% Anomalies
- The ensemble successfully bridges the detection gap by identifying multivariate and graphical structuring patterns without spiking the false positive rate.


## ReconciliationAnalyzer
```
Not implemented yet
```


## CategorizationAnalyzer
```
Categorization Model Evaluation:
Macro-F1 Score: 0.5102
Labels: ['auto_and_transport', 'crypto', 'electronics', 'food_and_dining', 'gambling', 'retail', 'unknown']
Confusion Matrix:
[[0 0 0 0 0 1 0]
 [0 1 0 0 0 0 0]
 [0 0 0 0 0 1 0]
 [0 0 0 1 0 0 0]
 [0 0 0 0 1 0 0]
 [0 0 0 0 0 2 0]
 [0 0 0 0 0 1 0]]
```


## DisputeAnalyzer
```
Dispute Workflow Metrics:
Total Disputes: 50
Open: 15
Win Rate: 42.9% (15 won, 20 lost)

```


## ReportingAnalyzer
```
No reports to evaluate.
```
