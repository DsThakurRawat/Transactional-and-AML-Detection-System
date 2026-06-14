from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, Numeric, String, Integer, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from core.store.models import Base

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    source: Mapped[str] = mapped_column(String, index=True) # "internal" vs "processor"
    external_ref: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3))
    direction: Mapped[str] = mapped_column(String) # "credit" / "debit"
    transaction_date: Mapped[datetime] = mapped_column(DateTime)
    settlement_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String) # "completed", "pending", "failed"
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False) # For synthetic testing
    anomaly_type: Mapped[str | None] = mapped_column(String, nullable=True)

class Discrepancy(Base):
    __tablename__ = "discrepancies"
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    type: Mapped[str] = mapped_column(String) # missing, amount_mismatch, duplicate, timing, status_mismatch
    internal_entry_id: Mapped[str | None] = mapped_column(String, nullable=True)
    processor_entry_id: Mapped[str | None] = mapped_column(String, nullable=True)
    amount_diff: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
