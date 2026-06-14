import uuid
import pandas as pd
from decimal import Decimal
from datetime import datetime, timedelta
import random

def generate_reconciliation_data(num_records: int = 1000, anomaly_rate: float = 0.05, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    base_time = datetime(2026, 1, 1)
    
    records = []
    
    num_anomalies = int(num_records * anomaly_rate)
    normal_records = num_records - num_anomalies
    
    # 1. Normal Records (matching perfectly or with slight timing diffs)
    for i in range(normal_records):
        tx_id = f"tx_{i}_{uuid.uuid4().hex[:8]}"
        amount = round(random.uniform(10.0, 5000.0), 2)
        tx_date = base_time + timedelta(minutes=random.randint(0, 43200)) # 30 days
        
        # Internal
        records.append({
            "id": f"int_{tx_id}",
            "source": "internal",
            "external_ref": tx_id,
            "amount": amount,
            "currency": "USD",
            "direction": "credit",
            "transaction_date": tx_date,
            "settlement_date": tx_date,
            "status": "completed",
            "is_anomaly": False,
            "anomaly_type": None
        })
        
        # Processor (with slight settlement delay)
        records.append({
            "id": f"proc_{tx_id}",
            "source": "processor",
            "external_ref": f"PROC-{tx_id}", # Simulator prefix
            "amount": amount,
            "currency": "USD",
            "direction": "credit",
            "transaction_date": tx_date,
            "settlement_date": tx_date + timedelta(days=random.randint(0, 2)),
            "status": "completed",
            "is_anomaly": False,
            "anomaly_type": None
        })
        
    # 2. Anomalies
    anomaly_types = ["missing_processor", "missing_internal", "amount_mismatch", "duplicate_processor", "status_mismatch"]
    for i in range(num_anomalies):
        tx_id = f"tx_anom_{i}_{uuid.uuid4().hex[:8]}"
        amount = round(random.uniform(10.0, 5000.0), 2)
        tx_date = base_time + timedelta(minutes=random.randint(0, 43200))
        atype = random.choice(anomaly_types)
        
        int_rec = {
            "id": f"int_{tx_id}",
            "source": "internal",
            "external_ref": tx_id,
            "amount": amount,
            "currency": "USD",
            "direction": "credit",
            "transaction_date": tx_date,
            "settlement_date": tx_date,
            "status": "completed",
            "is_anomaly": True,
            "anomaly_type": atype
        }
        
        proc_rec = {
            "id": f"proc_{tx_id}",
            "source": "processor",
            "external_ref": f"PROC-{tx_id}",
            "amount": amount,
            "currency": "USD",
            "direction": "credit",
            "transaction_date": tx_date,
            "settlement_date": tx_date + timedelta(days=1),
            "status": "completed",
            "is_anomaly": True,
            "anomaly_type": atype
        }
        
        if atype == "missing_processor":
            records.append(int_rec)
        elif atype == "missing_internal":
            records.append(proc_rec)
        elif atype == "amount_mismatch":
            proc_rec["amount"] = round(amount * 1.1, 2)
            records.extend([int_rec, proc_rec])
        elif atype == "duplicate_processor":
            records.extend([int_rec, proc_rec])
            dup_proc = proc_rec.copy()
            dup_proc["id"] = f"proc_dup_{tx_id}"
            records.append(dup_proc)
        elif atype == "status_mismatch":
            proc_rec["status"] = "pending"
            records.extend([int_rec, proc_rec])
            
    df = pd.DataFrame(records)
    # Shuffle
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    return df
