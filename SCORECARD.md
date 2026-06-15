# Platform Scorecard (All Analyzers)
    
This scorecard evaluates the end-to-end performance of all platform analyzers.

## AML Detection Lift (Rules vs Ensemble)
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
Failed to evaluate: (psycopg2.OperationalError) could not translate host name "...your-managed-postgres..." to address: Name or service not known

(Background on this error at: https://sqlalche.me/e/20/e3q8)


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
Failed to evaluate: (psycopg2.OperationalError) could not translate host name "...your-managed-postgres..." to address: Name or service not known

(Background on this error at: https://sqlalche.me/e/20/e3q8)


## ReportingAnalyzer
Failed to evaluate: (psycopg2.OperationalError) could not translate host name "...your-managed-postgres..." to address: Name or service not known

(Background on this error at: https://sqlalche.me/e/20/e3q8)
