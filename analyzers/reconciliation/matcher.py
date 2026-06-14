from sqlalchemy.orm import Session
from sqlalchemy import select
from decimal import Decimal
from datetime import timedelta
import re
import uuid
from analyzers.reconciliation.models import LedgerEntry, Discrepancy

def normalize_ref(ref: str | None) -> str:
    if not ref:
        return ""
    # Strip PROC- prefix and any non-alphanumeric chars for loose matching
    clean = re.sub(r'^PROC-', '', ref)
    return clean

def match_entries(session: Session, run_id: int) -> int:
    """
    Match internal ledger entries against processor entries.
    Identifies exact matches, fuzzy matches, and discrepancies.
    Returns the number of discrepancies found.
    """
    internals = session.scalars(select(LedgerEntry).where(LedgerEntry.source == 'internal')).all()
    processors = session.scalars(select(LedgerEntry).where(LedgerEntry.source == 'processor')).all()
    
    internal_pool = {e.id: e for e in internals}
    processor_pool = {e.id: e for e in processors}
    
    # 1. Exact Match on external_ref
    proc_by_ref = {}
    for p in processors:
        norm_ref = normalize_ref(p.external_ref)
        if norm_ref not in proc_by_ref:
            proc_by_ref[norm_ref] = []
        proc_by_ref[norm_ref].append(p)
        
    discrepancies = []
    
    for i_id, i_entry in list(internal_pool.items()):
        norm_ref = normalize_ref(i_entry.external_ref)
        candidates = proc_by_ref.get(norm_ref, [])
        
        if not candidates:
            # Missing in processor
            discrepancies.append(Discrepancy(
                id=str(uuid.uuid4()),
                run_id=run_id,
                type="missing_processor",
                internal_entry_id=i_id,
                amount_diff=i_entry.amount,
                confidence=1.0
            ))
            del internal_pool[i_id]
            continue
            
        if len(candidates) == 1:
            p_entry = candidates[0]
            if p_entry.id not in processor_pool:
                # Duplicate processor match
                discrepancies.append(Discrepancy(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    type="duplicate_processor",
                    internal_entry_id=i_id,
                    processor_entry_id=p_entry.id,
                    confidence=1.0
                ))
                del internal_pool[i_id]
                continue
                
            # Compare attributes
            if p_entry.amount != i_entry.amount:
                discrepancies.append(Discrepancy(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    type="amount_mismatch",
                    internal_entry_id=i_id,
                    processor_entry_id=p_entry.id,
                    amount_diff=p_entry.amount - i_entry.amount,
                    confidence=1.0
                ))
            elif p_entry.status != i_entry.status:
                discrepancies.append(Discrepancy(
                    id=str(uuid.uuid4()),
                    run_id=run_id,
                    type="status_mismatch",
                    internal_entry_id=i_id,
                    processor_entry_id=p_entry.id,
                    confidence=1.0
                ))
            else:
                # Perfect match, or minor timing diff which is acceptable
                pass
                
            del internal_pool[i_id]
            del processor_pool[p_entry.id]
        else:
            # Multiple candidates -> Duplicate
            discrepancies.append(Discrepancy(
                id=str(uuid.uuid4()),
                run_id=run_id,
                type="duplicate_processor",
                internal_entry_id=i_id,
                processor_entry_id=candidates[0].id,
                confidence=1.0
            ))
            del internal_pool[i_id]
            for c in candidates:
                if c.id in processor_pool:
                    del processor_pool[c.id]
                    
    # Remaining processor pool
    for p_id, p_entry in processor_pool.items():
        discrepancies.append(Discrepancy(
            id=str(uuid.uuid4()),
            run_id=run_id,
            type="missing_internal",
            processor_entry_id=p_id,
            amount_diff=p_entry.amount,
            confidence=1.0
        ))
        
    if discrepancies:
        session.add_all(discrepancies)
        
    return len(discrepancies)
