import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy import select
from core.store.models import Finding
from analyzers.disputes.models import Dispute
from analyzers.disputes.analyzer import DisputeAnalyzer
from tests.aml.test_v2_and_v3 import db_session_factory

def test_disputes_analyzer(db_session_factory):
    with db_session_factory() as session:
        now = datetime.now(timezone.utc)
        d1 = Dispute(
            dispute_id="disp_1",
            transaction_id="tx_1",
            reason_code="fraud",
            amount=Decimal("100.00"),
            currency="USD",
            status="open",
            created_at=now - timedelta(days=10),
            deadline=now + timedelta(days=2) # Urgent!
        )
        d2 = Dispute(
            dispute_id="disp_2",
            transaction_id="tx_2",
            reason_code="fraud",
            amount=Decimal("200.00"),
            currency="USD",
            status="open",
            created_at=now - timedelta(days=10),
            deadline=now + timedelta(days=10) # Not urgent
        )
        session.add_all([d1, d2])
        session.commit()
        
        analyzer = DisputeAnalyzer()
        result = analyzer.run(session, {})
        
        assert result.findings_count == 1
        
        findings = session.scalars(select(Finding).where(Finding.analyzer == "disputes")).all()
        assert len(findings) == 1
        assert findings[0].entity_id == "disp_1"
