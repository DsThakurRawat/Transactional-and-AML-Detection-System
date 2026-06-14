from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import DateTime, Numeric, String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column
from core.store.models import Base

class Dispute(Base):
    __tablename__ = "disputes"
    
    dispute_id: Mapped[str] = mapped_column(String, primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String, index=True)
    reason_code: Mapped[str] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String, default="open") # open, won, lost, represented
    created_at: Mapped[datetime] = mapped_column(DateTime)
    deadline: Mapped[datetime] = mapped_column(DateTime)
    evidence_collected: Mapped[bool] = mapped_column(Integer, default=0)
    rebuttal_draft: Mapped[str | None] = mapped_column(String, nullable=True)

class Case(Base):
    __tablename__ = "cases"
    
    case_id: Mapped[str] = mapped_column(String, primary_key=True)
    entity_type: Mapped[str] = mapped_column(String) # account, merchant
    entity_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="open")
    priority: Mapped[str] = mapped_column(String, default="medium")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
