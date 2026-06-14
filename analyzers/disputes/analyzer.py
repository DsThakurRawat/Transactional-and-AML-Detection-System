import uuid
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from core.analyzer import Analyzer, RunResult
from core.registry import register
from core.store.models import Finding
from core.config import get_settings
from analyzers.disputes.models import Dispute, Case

class DisputeAnalyzer(Analyzer):
    name = "disputes"

    def required_inputs(self) -> list[str]:
        return ["disputes"]

    def run(self, session: Session, config: dict) -> RunResult:
        settings = get_settings()
        
        # Clear prior findings
        session.execute(delete(Finding).where(Finding.analyzer == "disputes"))
        session.commit()
        
        disputes = session.scalars(select(Dispute)).all()
        if not disputes:
            return RunResult(0, "No disputes to process")
            
        findings_count = 0
        now = datetime.now(timezone.utc)
        
        for d in disputes:
            # Check for urgent deadlines
            if d.status == "open":
                # Ensure timezone aware
                deadline = d.deadline
                if deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=timezone.utc)
                    
                days_left = (deadline - now).days
                
                if days_left <= 3:
                    # Urgent finding
                    finding = Finding(
                        id=str(uuid.uuid4()),
                        analyzer="disputes",
                        entity_type="dispute",
                        entity_id=d.dispute_id,
                        finding_type="urgent_deadline",
                        score=100.0 if days_left <= 1 else 75.0,
                        band="critical" if days_left <= 1 else "high",
                        status="open",
                        summary=f"Dispute {d.dispute_id} due in {days_left} days",
                        payload_json={"reason_code": d.reason_code, "deadline": d.deadline.isoformat(), "amount": float(d.amount)}
                    )
                    session.add(finding)
                    findings_count += 1
                    
        session.commit()
        return RunResult(findings_count, f"Processed {len(disputes)} disputes, created {findings_count} findings")

    def evaluate(self, session: Session) -> Optional[str]:
        return None

register(DisputeAnalyzer())
