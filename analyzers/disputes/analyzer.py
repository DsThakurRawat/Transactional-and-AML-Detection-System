import uuid
import json
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, func
from core.analyzer import Analyzer, RunResult
from core.registry import register
from core.store.models import Finding, Transaction
from core.config import get_settings
from analyzers.disputes.models import Dispute, Case
from core.llm import get_groq_client

# Map dispute reason codes to the evidence needed for a strong rebuttal
REASON_CODE_EVIDENCE_MAP = {
    "10.4": ["transaction_receipt", "avs_match", "cvv_match"], # Fraud
    "4837": ["transaction_receipt", "avs_match", "cvv_match", "login_ip_match"], # Fraud (Mastercard)
    "13.1": ["delivery_proof", "tracking_number", "customer_signature"], # Merchandise not received
    "30": ["refund_policy", "communication_logs", "delivery_proof"], # Services not provided or merchandise not as described
    "85": ["refund_policy", "refund_receipt"], # Credit not processed
    "duplicate": ["transaction_receipt1", "transaction_receipt2"],
}

class DisputeAnalyzer(Analyzer):
    name = "disputes"

    def required_inputs(self) -> list[str]:
        return ["disputes"]

    def run(self, session: Session, config: dict) -> RunResult:
        settings = get_settings()
        
        # Clear prior findings for idempotency
        session.execute(delete(Finding).where(Finding.analyzer == "disputes"))
        session.commit()
        
        disputes = session.scalars(select(Dispute)).all()
        if not disputes:
            return RunResult(0, "No disputes to process")
            
        client = get_groq_client()
        findings_count = 0
        now = datetime.now(timezone.utc)
        
        for d in disputes:
            if d.status == "open":
                # Ensure timezone aware
                deadline = d.deadline
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                    
                days_left = (deadline - now).days
                
                # Check for required evidence based on reason code
                required_evidence = REASON_CODE_EVIDENCE_MAP.get(d.reason_code, ["transaction_receipt"])
                
                # State machine: Collect Evidence -> Draft Rebuttal -> Represent -> Won/Lost
                if not d.evidence_collected:
                    # Simulate evidence collection
                    tx = session.scalar(select(Transaction).where(Transaction.transaction_id == d.transaction_id))
                    evidence = {"tx": {"amount": float(tx.amount), "merchant": tx.merchant} if tx else {}}
                    d.evidence_collected = True
                    
                    # Generate Rebuttal
                    if client and tx:
                        prompt = f"""
                        Draft a chargeback rebuttal letter for dispute {d.dispute_id}.
                        Reason Code: {d.reason_code}
                        Transaction: {evidence['tx']}
                        Required Evidence: {required_evidence}
                        
                        Keep it professional, concise, and refer to the provided evidence.
                        """
                        try:
                            response = client.chat.completions.create(
                                messages=[{"role": "user", "content": prompt}],
                                model=settings.groq_model,
                                temperature=0.0
                            )
                            d.rebuttal_draft = response.choices[0].message.content
                        except Exception:
                            pass
                
                # Emit finding if deadline is approaching
                if days_left <= 3:
                    finding = Finding(
                        id=str(uuid.uuid4()),
                        analyzer="disputes",
                        entity_type="dispute",
                        entity_id=d.dispute_id,
                        finding_type="urgent_deadline",
                        score=100.0,
                        band="critical",
                        status="needs_review",
                        summary=f"Dispute {d.dispute_id[:8]} deadline in {days_left} days",
                        payload_json={
                            "reason_code": d.reason_code,
                            "days_left": days_left,
                            "rebuttal_drafted": bool(d.rebuttal_draft),
                            "required_evidence": required_evidence
                        }
                    )
                    session.add(finding)
                    findings_count += 1
                elif not d.rebuttal_draft:
                    # Need evidence or rebuttal
                    finding = Finding(
                        id=str(uuid.uuid4()),
                        analyzer="disputes",
                        entity_type="dispute",
                        entity_id=d.dispute_id,
                        finding_type="missing_evidence",
                        score=60.0,
                        band="high",
                        status="open",
                        summary=f"Dispute {d.dispute_id[:8]} missing rebuttal/evidence",
                        payload_json={"reason_code": d.reason_code, "required_evidence": required_evidence}
                    )
                    session.add(finding)
                    findings_count += 1
                    
        session.commit()
        return RunResult(findings_count, f"Processed {len(disputes)} disputes, flagged {findings_count}")

    def evaluate(self, session: Session) -> Optional[str]:
        # Workflow metrics for disputes
        total = session.scalar(select(func.count(Dispute.dispute_id)))
        if not total:
            return "No disputes to evaluate."
            
        open_count = session.scalar(select(func.count(Dispute.dispute_id)).where(Dispute.status == 'open'))
        won_count = session.scalar(select(func.count(Dispute.dispute_id)).where(Dispute.status == 'won'))
        lost_count = session.scalar(select(func.count(Dispute.dispute_id)).where(Dispute.status == 'lost'))
        
        win_rate = (won_count / (won_count + lost_count)) * 100 if (won_count + lost_count) > 0 else 0
        
        report = f"Dispute Workflow Metrics:\n"
        report += f"Total Disputes: {total}\n"
        report += f"Open: {open_count}\n"
        report += f"Win Rate: {win_rate:.1f}% ({won_count} won, {lost_count} lost)\n"
        return report

register(DisputeAnalyzer())
