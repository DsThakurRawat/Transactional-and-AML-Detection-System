import pytest
from sqlalchemy import select
from core.store.db import Base
from core.store.models import Finding
from analyzers.reconciliation.models import LedgerEntry, Discrepancy
from analyzers.reconciliation.analyzer import ReconciliationAnalyzer
from data.reconciliation import generate_reconciliation_data
from tests.aml.test_v2_and_v3 import db_session_factory

def test_reconciliation_analyzer(db_session_factory):
    # Generate data
    df = generate_reconciliation_data(num_records=100, anomaly_rate=0.1, seed=42)
    
    with db_session_factory() as session:
        # Inject data
        for _, row in df.iterrows():
            entry = LedgerEntry(**row.to_dict())
            session.add(entry)
        session.commit()
        
        # Run analyzer
        analyzer = ReconciliationAnalyzer()
        result = analyzer.run(session, {})
        
        # Assertions
        assert result.findings_count > 0
        
        # Check Findings
        findings = session.scalars(select(Finding).where(Finding.analyzer == "reconciliation")).all()
        assert len(findings) == result.findings_count
        
        # Check Discrepancies
        discrepancies = session.scalars(select(Discrepancy)).all()
        assert len(discrepancies) == result.findings_count
