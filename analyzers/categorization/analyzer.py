import uuid
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from core.analyzer import Analyzer, RunResult
from core.registry import register
from core.store.models import Finding, Transaction
from core.config import get_settings
from analyzers.categorization.models import TransactionCategory
from analyzers.categorization.engine import categorize_merchant

class CategorizationAnalyzer(Analyzer):
    name = "categorization"

    def required_inputs(self) -> list[str]:
        return ["transactions"]

    def run(self, session: Session, config: dict) -> RunResult:
        settings = get_settings()
        
        # 1. Clear prior state for idempotency
        session.execute(delete(Finding).where(Finding.analyzer == "categorization"))
        session.execute(delete(TransactionCategory))
        session.commit()
        
        transactions = session.scalars(select(Transaction)).all()
        if not transactions:
            return RunResult(0, "No transactions to categorize")
            
        findings_count = 0
        categories = []
        for tx in transactions:
            category, conf, source = categorize_merchant(tx.merchant)
            cat_obj = TransactionCategory(
                transaction_id=tx.transaction_id,
                category=category,
                confidence=conf,
                source=source
            )
            categories.append(cat_obj)
            
            # Emit finding for high-risk categories or low confidence
            status = "needs_review" if conf < 0.7 else "open"
            if category in ["crypto", "gambling"]:
                finding = Finding(
                    id=str(uuid.uuid4()),
                    analyzer="categorization",
                    entity_type="transaction",
                    entity_id=tx.transaction_id,
                    finding_type="high_risk_category",
                    score=80.0 if category == "crypto" else 90.0,
                    band="high" if category == "crypto" else "critical",
                    status=status,
                    summary=f"Transaction assigned to high-risk category: {category} (conf: {conf:.2f})",
                    payload_json={"merchant": tx.merchant, "category": category, "confidence": conf, "source": source}
                )
                session.add(finding)
                findings_count += 1
                
        session.add_all(categories)
        session.commit()
        
        return RunResult(findings_count, f"Categorized {len(transactions)} transactions, flagged {findings_count}")

    def evaluate(self, session: Session) -> Optional[str]:
        from sklearn.metrics import f1_score, confusion_matrix
        from analyzers.categorization.engine import categorize_merchant
        
        # Labeled test set representing the messy strings the generator produces
        test_data = [
            ("PAYPAL *WALMART STORE INC", "retail"),
            ("POS DEBIT MCDONALDS #445", "food_and_dining"),
            ("WWW.BINANCE LLC", "crypto"),
            ("SQ *DRAFTKINGS", "gambling"),
            ("TST* APPLE STORE", "electronics"),
            ("AMAZON", "retail"),
            ("CHEVRON STORE 123", "auto_and_transport"),
            ("UNKNOWN MERCHANT", "unknown")
        ]
        
        y_true = [t[1] for t in test_data]
        y_pred = []
        for merchant, _ in test_data:
            cat, _, _ = categorize_merchant(merchant)
            y_pred.append(cat)
            
        f1 = f1_score(y_true, y_pred, average='macro', zero_division=0)
        cm = confusion_matrix(y_true, y_pred)
        
        labels = sorted(list(set(y_true + y_pred)))
        
        report = f"Categorization Model Evaluation:\nMacro-F1 Score: {f1:.4f}\n"
        report += f"Labels: {labels}\n"
        report += f"Confusion Matrix:\n{cm}"
        return report

register(CategorizationAnalyzer())
