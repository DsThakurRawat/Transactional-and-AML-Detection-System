from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.storage.models import Transaction, Flag
from app.config import get_settings

class RuleFlag:
    def __init__(self, rule_name: str, reason: str, severity: str):
        self.rule_name = rule_name
        self.reason = reason
        self.severity = severity

class Rule:
    name: str = "base_rule"
    
    def evaluate(self, tx: Transaction, session: Session) -> Optional[RuleFlag]:
        raise NotImplementedError

class LargeAmountRule(Rule):
    name = "amount"
    
    def evaluate(self, tx: Transaction, session: Session) -> Optional[RuleFlag]:
        settings = get_settings()
        if tx.currency == "INR" and float(tx.amount) > settings.rule_amount_threshold_inr:
            return RuleFlag(rule_name=self.name, reason=f"Amount {tx.amount} exceeds INR threshold {settings.rule_amount_threshold_inr}", severity="high")
        elif tx.currency != "INR" and float(tx.amount) > settings.rule_amount_threshold_usd:
            return RuleFlag(rule_name=self.name, reason=f"Amount {tx.amount} exceeds USD threshold {settings.rule_amount_threshold_usd}", severity="high")
        return None

class HighRiskMCCRule(Rule):
    name = "high_risk_mcc"
    
    def evaluate(self, tx: Transaction, session: Session) -> Optional[RuleFlag]:
        settings = get_settings()
        if tx.merchant_category in settings.rule_high_risk_mcc:
            return RuleFlag(rule_name=self.name, reason=f"Transaction in high-risk merchant category: {tx.merchant_category}", severity="medium")
        return None

class OddHourRule(Rule):
    name = "odd_hour"
    
    def evaluate(self, tx: Transaction, session: Session) -> Optional[RuleFlag]:
        settings = get_settings()
        if settings.rule_odd_hour_start <= tx.timestamp.hour <= settings.rule_odd_hour_end:
            return RuleFlag(rule_name=self.name, reason=f"Transaction at odd hour: {tx.timestamp.hour}:00", severity="low")
        return None

class VelocityRule(Rule):
    name = "velocity"
    
    def evaluate(self, tx: Transaction, session: Session) -> Optional[RuleFlag]:
        settings = get_settings()
        window_start = tx.timestamp - timedelta(minutes=settings.rule_velocity_window_minutes)
        
        stmt = select(Transaction).where(
            Transaction.account_id == tx.account_id,
            Transaction.timestamp <= tx.timestamp,
            Transaction.timestamp >= window_start,
            Transaction.transaction_id != tx.transaction_id
        )
        recent_txs = session.scalars(stmt).all()
        
        if len(recent_txs) + 1 >= settings.rule_velocity_count:
            return RuleFlag(rule_name=self.name, reason=f"{len(recent_txs) + 1} transactions within {settings.rule_velocity_window_minutes} minutes", severity="critical")
        return None

class StructuringRule(Rule):
    name = "structuring"
    
    def evaluate(self, tx: Transaction, session: Session) -> Optional[RuleFlag]:
        settings = get_settings()
        window_start = tx.timestamp - timedelta(hours=settings.rule_structuring_window_hours)
        
        if tx.currency == "INR":
            threshold = settings.rule_structuring_threshold_inr
        else:
            threshold = settings.rule_structuring_threshold_usd
            
        stmt = select(Transaction).where(
            Transaction.account_id == tx.account_id,
            Transaction.timestamp <= tx.timestamp,
            Transaction.timestamp >= window_start
        )
        recent_txs = session.scalars(stmt).all()
        
        total_sum = sum(float(t.amount) for t in recent_txs)
        
        if len(recent_txs) > 1 and threshold * 0.85 <= total_sum < threshold:
            return RuleFlag(rule_name=self.name, reason=f"Structuring pattern detected: {len(recent_txs)} transactions summing to {total_sum:.2f} within {settings.rule_structuring_window_hours} hours", severity="critical")
        return None

class CountryMismatchRule(Rule):
    name = "country_mismatch"
    
    def evaluate(self, tx: Transaction, session: Session) -> Optional[RuleFlag]:
        stmt = select(Transaction.country).where(
            Transaction.account_id == tx.account_id,
            Transaction.timestamp < tx.timestamp
        ).distinct()
        previous_countries = session.scalars(stmt).all()
        
        if previous_countries and tx.country not in previous_countries:
            return RuleFlag(rule_name=self.name, reason=f"Country mismatch: {tx.country} not in account history", severity="high")
        return None

class RuleEngine:
    def __init__(self):
        self.rules: List[Rule] = [
            LargeAmountRule(),
            HighRiskMCCRule(),
            OddHourRule(),
            VelocityRule(),
            StructuringRule(),
            CountryMismatchRule()
        ]
        
    def evaluate_transaction(self, tx: Transaction, session: Session) -> List[Flag]:
        flags = []
        for rule in self.rules:
            result = rule.evaluate(tx, session)
            if result:
                flag = Flag(
                    transaction_id=tx.transaction_id,
                    rule_name=result.rule_name,
                    reason=result.reason,
                    severity=result.severity
                )
                flags.append(flag)
        return flags

engine = RuleEngine()
