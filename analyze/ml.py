import os
import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score

MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "iso_forest.joblib")

class ClassicalAnomalyDetector:
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        # Isolation Forest is our primary unsupervised model
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05, # Expect ~5% anomalies
            random_state=self.random_state,
            n_jobs=-1
        )
        self.feature_columns = None

    def train(self, df_features: pd.DataFrame):
        # Drop ID columns for training
        X = df_features.drop(columns=["transaction_id", "account_id"], errors="ignore")
        self.feature_columns = X.columns.tolist()
        
        self.model.fit(X)

    def predict(self, df_features: pd.DataFrame) -> pd.Series:
        # Align features
        X = df_features.copy()
        for col in self.feature_columns:
            if col not in X.columns:
                X[col] = 0
        X = X[self.feature_columns]
        
        # Output: -1 for anomaly, 1 for normal
        preds = self.model.predict(X)
        
        # We want to return an anomaly score or a binary flag (True if anomaly)
        return pd.Series(preds == -1, index=df_features.index)

    def save(self, path: str = MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"model": self.model, "features": self.feature_columns}, path)

    @classmethod
    def load(cls, path: str = MODEL_PATH):
        if not os.path.exists(path):
            return None
        
        data = joblib.load(path)
        detector = cls()
        detector.model = data["model"]
        detector.feature_columns = data["features"]
        return detector

def evaluate_supervised(df_train_features: pd.DataFrame, df_test_features: pd.DataFrame, y_train: pd.Series, y_test: pd.Series, random_state: int = 42):
    """
    Supervised comparison harness.
    Trains a Random Forest with class_weight='balanced_subsample' to handle the heavy imbalance.
    """
    X_train = df_train_features.drop(columns=["transaction_id", "account_id"], errors="ignore")
    X_test = df_test_features.drop(columns=["transaction_id", "account_id"], errors="ignore")
    
    # Align test features to train
    for col in X_train.columns:
        if col not in X_test.columns:
            X_test[col] = 0
    X_test = X_test[X_train.columns]

    clf = RandomForestClassifier(
        n_estimators=100,
        class_weight='balanced_subsample',
        random_state=random_state,
        n_jobs=-1
    )
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    
    return {
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "pr_auc": average_precision_score(y_test, y_prob)
    }
