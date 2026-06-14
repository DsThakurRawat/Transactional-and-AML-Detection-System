import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import select
from store.models import Transaction, AccountBaseline

def extract_features(session: Session, transactions: list[Transaction] = None) -> pd.DataFrame:
    """
    Extracts engineered features for ML detection from a list of transactions.
    If no transactions provided, fetches all from DB.
    Merges with AccountBaseline to compute context-aware features.
    
    WARNING: Does not include target labels to prevent leakage.
    """
    if not transactions:
        transactions = session.scalars(select(Transaction)).all()
        
    if not transactions:
        return pd.DataFrame()

    # Load baselines
    baselines = session.scalars(select(AccountBaseline)).all()
    baseline_map = {b.account_id: b for b in baselines}
    
    features_list = []
    
    # Precompute global median for peer/population comparison
    all_amounts = [float(tx.amount) for tx in transactions]
    global_median = float(np.median(all_amounts)) if all_amounts else 0.0

    for tx in transactions:
        b = baseline_map.get(tx.account_id)
        
        # Base features
        amount = float(tx.amount)
        log_amount = np.log1p(amount) # log1p handles amount 0 safely
        hour = tx.timestamp.hour
        day_of_week = tx.timestamp.weekday()
        
        # Context-aware features (default to 0/False if no baseline)
        if b and b.tx_count >= 10:
            robust_z = 0.6745 * (amount - float(b.amount_median)) / float(b.amount_mad)
            is_new_country = 1 if tx.country not in b.seen_countries else 0
            is_new_mcc = 1 if tx.merchant_category not in b.seen_mccs else 0
            tx_count = b.tx_count
        else:
            robust_z = 0.0
            is_new_country = 0
            is_new_mcc = 0
            tx_count = 0
            
        # Peer feature
        vs_global_median = amount / global_median if global_median > 0 else 0.0
        
        features_list.append({
            "transaction_id": tx.transaction_id,
            "account_id": tx.account_id,
            "amount": amount,
            "log_amount": log_amount,
            "hour": hour,
            "day_of_week": day_of_week,
            "robust_z_score": robust_z,
            "is_new_country": is_new_country,
            "is_new_mcc": is_new_mcc,
            "tx_count": tx_count,
            "vs_global_median": vs_global_median,
            "channel": tx.channel,
            "mcc": tx.merchant_category
        })
        
    df = pd.DataFrame(features_list)
    
    # Categorical Encoding (One-Hot)
    # We strictly only one-hot encode. No target encoding to prevent leakage.
    df = pd.get_dummies(df, columns=["channel", "mcc"], drop_first=True)
    
    return df
