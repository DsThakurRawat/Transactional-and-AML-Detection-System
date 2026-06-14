import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from core.analyzer import Analyzer, RunResult
from core.registry import register
from core.store.models import Finding
from core.config import get_settings
from analyzers.reconciliation.models import LedgerEntry, Discrepancy
from analyzers.reconciliation.matcher import match_entries

class ReconciliationAnalyzer(Analyzer):
    name = "reconciliation"

    def required_inputs(self) -> list[str]:
        return ["ledger_entries"]

    def run(self, session: Session, config: dict) -> RunResult:
        settings = get_settings()
        
        # 1. Clear prior state for idempotency
        session.execute(delete(Finding).where(Finding.analyzer == "reconciliation"))
        session.execute(delete(Discrepancy))
        session.commit()
        
        # 2. Check inputs
        count = session.query(LedgerEntry).count()
        if count == 0:
            return RunResult(0, "No ledger entries to reconcile")
            
        # 3. Match
        discrepancy_count = match_entries(session, run_id=0)
        session.commit()
        
        # 4. Generate Findings
        discrepancies = session.scalars(select(Discrepancy)).all()
        findings_count = 0
        for d in discrepancies:
            # Reconstruct entity context
            summary = f"Discrepancy: {d.type}"
            if d.amount_diff:
                summary += f" (Diff: {float(d.amount_diff)})"
                
            entity_id = d.internal_entry_id or d.processor_entry_id or d.id
                
            finding = Finding(
                id=str(uuid.uuid4()),
                analyzer="reconciliation",
                entity_type="ledger_entry",
                entity_id=entity_id,
                finding_type=d.type,
                score=100.0 if d.type in ["missing_processor", "missing_internal", "amount_mismatch"] else 50.0,
                band="critical" if d.type in ["missing_processor", "missing_internal", "amount_mismatch"] else "medium",
                status="open",
                summary=summary,
                payload_json={"internal_entry_id": d.internal_entry_id, "processor_entry_id": d.processor_entry_id, "amount_diff": float(d.amount_diff) if d.amount_diff else None}
            )
            session.add(finding)
            findings_count += 1
            
        session.commit()
        
        return RunResult(findings_count, f"Reconciled {count} entries, found {findings_count} breaks")

    def evaluate(self, session: Session) -> Optional[str]:
        # precision and recall for anomalies
        from sqlalchemy import func
        # Actual evaluation would compare is_anomaly on LedgerEntry vs Findings
        return "Not implemented yet"

register(ReconciliationAnalyzer())
