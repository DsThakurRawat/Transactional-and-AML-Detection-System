import pytest
import os
import numpy as np
import pandas as pd
from sqlalchemy import select
from sklearn.model_selection import train_test_split

from store.models import Transaction, Score
from analyze.features import extract_features
from analyze.ml import ClassicalAnomalyDetector, evaluate_supervised
from analyze.baselines import compute_baselines
from tests.test_v2_and_v3 import db_session_factory, setup_data

def test_feature_correctness_and_no_leakage(setup_data, db_session_factory):
    """Ensure features extract properly without NaNs/infs and contain no target leakage."""
    with db_session_factory() as session:
        compute_baselines(session)
        df_features = extract_features(session)
        
    assert not df_features.empty
    
    # Check for leakage
    leakage_cols = ['is_anomaly', 'anomaly_type']
    for col in leakage_cols:
        assert col not in df_features.columns, f"Target leakage found: {col} in features!"
        
    # Check basic health
    assert not df_features.isnull().values.any(), "Found NaNs in feature matrix!"
    assert not df_features.isin([np.inf, -np.inf]).values.any(), "Found infs in feature matrix!"
    assert 'log_amount' in df_features.columns
    assert 'robust_z_score' in df_features.columns

def test_ml_lifecycle_and_graceful_degradation(setup_data, db_session_factory, tmp_path):
    """Test train, save, load, and graceful degradation."""
    model_path = str(tmp_path / "iso_forest.joblib")
    
    # Graceful degradation (no model)
    loaded_empty = ClassicalAnomalyDetector.load(model_path)
    assert loaded_empty is None
    
    with db_session_factory() as session:
        compute_baselines(session)
        df_features = extract_features(session)
        
    # Train & Save
    detector = ClassicalAnomalyDetector(random_state=42)
    detector.train(df_features)
    detector.save(model_path)
    
    assert os.path.exists(model_path)
    
    # Load & Score
    loaded_model = ClassicalAnomalyDetector.load(model_path)
    assert loaded_model is not None
    preds = loaded_model.predict(df_features)
    
    assert len(preds) == len(df_features)
    assert preds.dtype == bool

def test_evaluation_metrics_and_lift(setup_data, db_session_factory):
    """
    Test the supervised comparison, account-split leakage prevention,
    and measure operational lift (FPR reduction vs rules-only).
    """
    df_labels = setup_data # df_final with is_anomaly
    
    with db_session_factory() as session:
        compute_baselines(session)
        df_features = extract_features(session)
        
    # Merge labels to prepare for evaluation
    df_merged = df_features.merge(df_labels[['transaction_id', 'account_id', 'is_anomaly']], on=['transaction_id', 'account_id'])
    
    # Account-based train/test split to prevent baseline leakage
    accounts = df_merged['account_id'].unique()
    train_accs, test_accs = train_test_split(accounts, test_size=0.3, random_state=42)
    
    df_train = df_merged[df_merged['account_id'].isin(train_accs)]
    df_test = df_merged[df_merged['account_id'].isin(test_accs)]
    
    # Isolation Forest Lift Check on Test Set
    detector = ClassicalAnomalyDetector(random_state=42)
    detector.train(df_train)
    iso_preds = detector.predict(df_test)
    
    # Compare with Rule-Based Score
    # We will simulate the Rules Score by aggregating the rule engine output
    with db_session_factory() as session:
        scores = session.scalars(select(Score)).all()
        score_map = {s.transaction_id: s.score for s in scores}
        
    df_test['rule_score'] = df_test['transaction_id'].map(score_map).fillna(0)
    df_test['rule_is_anomaly'] = df_test['rule_score'] >= 50 # Let's say >= 50 is an anomaly
    df_test['ml_is_anomaly'] = iso_preds.values
    
    # Combine rules + ML (simulate config weighting)
    # E.g. ml_is_anomaly adds 30 points to score
    df_test['combined_score'] = df_test['rule_score'] + df_test['ml_is_anomaly'] * 30
    df_test['combined_is_anomaly'] = df_test['combined_score'] >= 50
    
    true_anoms = df_test['is_anomaly'] == True
    true_normals = df_test['is_anomaly'] == False
    
    rules_recall = (df_test['rule_is_anomaly'] & true_anoms).sum() / true_anoms.sum() if true_anoms.sum() > 0 else 0
    rules_fpr = (df_test['rule_is_anomaly'] & true_normals).sum() / true_normals.sum() if true_normals.sum() > 0 else 0
    
    combined_recall = (df_test['combined_is_anomaly'] & true_anoms).sum() / true_anoms.sum() if true_anoms.sum() > 0 else 0
    combined_fpr = (df_test['combined_is_anomaly'] & true_normals).sum() / true_normals.sum() if true_normals.sum() > 0 else 0
    
    print(f"Rules: Recall {rules_recall:.3f}, FPR {rules_fpr:.3f}")
    print(f"Combined (Rules+ML): Recall {combined_recall:.3f}, FPR {combined_fpr:.3f}")
    
    # Supervised harness
    metrics = evaluate_supervised(
        df_train.drop(columns=['is_anomaly', 'rule_score', 'rule_is_anomaly', 'ml_is_anomaly', 'combined_score', 'combined_is_anomaly'], errors='ignore'),
        df_test.drop(columns=['is_anomaly', 'rule_score', 'rule_is_anomaly', 'ml_is_anomaly', 'combined_score', 'combined_is_anomaly'], errors='ignore'),
        df_train['is_anomaly'],
        df_test['is_anomaly']
    )
    
    print(f"Supervised RF Metrics: {metrics}")
    
    assert metrics["pr_auc"] > 0.1, f"PR-AUC is extremely low: {metrics['pr_auc']}"
    # Ensure no plain accuracy is being used here since classes are heavily imbalanced.
