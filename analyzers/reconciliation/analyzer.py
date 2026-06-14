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
        from analyzers.reconciliation.models import LedgerEntry
        from core.store.models import Finding
        from sqlalchemy import func
        
        # We can find total injected anomalies by looking at is_anomaly
        total_anomalies = session.scalar(select(func.count(LedgerEntry.id)).where(LedgerEntry.is_anomaly == True))
        if total_anomalies == 0:
            return "No anomalies found in ledger data. Cannot evaluate recall."
            
        # Actual evaluation compares is_anomaly on LedgerEntry vs Findings
        anomalous_entries = session.scalars(select(LedgerEntry).where(LedgerEntry.is_anomaly == True)).all()
        anomaly_ids = {e.id for e in anomalous_entries}
        
        findings = session.scalars(select(Finding).where(Finding.analyzer == "reconciliation")).all()
        flagged_ids = set()
        for f in findings:
            if f.payload_json:
                if f.payload_json.get("internal_entry_id"):
                    flagged_ids.add(f.payload_json.get("internal_entry_id"))
                if f.payload_json.get("processor_entry_id"):
                    flagged_ids.add(f.payload_json.get("processor_entry_id"))
                    
        true_positives = len(anomaly_ids.intersection(flagged_ids))
        false_positives = len(flagged_ids - anomaly_ids)
        
        recall = (true_positives / total_anomalies) * 100 if total_anomalies > 0 else 0.0
        precision = (true_positives / len(flagged_ids)) * 100 if flagged_ids else 100.0
        
        report = f"Reconciliation Evaluation:\n"
        report += f"Total Anomalies Injected: {total_anomalies}\n"
        report += f"Total Flagged by Matcher: {len(flagged_ids)}\n"
        report += f"Recall: {recall:.1f}%\n"
        report += f"Precision: {precision:.1f}%\n"
        
        return report

register(ReconciliationAnalyzer())
