import re
from typing import Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import numpy as np

# Description normalization
def normalize_merchant(merchant: str) -> str:
    if not merchant:
        return ""
    # Remove common prefixes/suffixes and punctuation
    text = merchant.upper()
    text = re.sub(r'(PAYPAL|SQ|TST|POS DEBIT|WWW\.| INC| LLC|\#\d+)', ' ', text)
    text = re.sub(r'[^A-Z0-9]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Exact Lookup Table (Stage 1)
LOOKUP_TABLE = {
    "WALMART": "retail",
    "TARGET": "retail",
    "MCDONALDS": "food_and_dining",
    "STARBUCKS": "food_and_dining",
    "AMAZON": "retail",
    "EBAY": "retail",
    "BINANCE": "crypto",
    "COINBASE": "crypto",
    "KRAKEN": "crypto",
    "DRAFTKINGS": "gambling",
    "FANDUEL": "gambling"
}

class CategorizationML:
    def __init__(self):
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2))),
            ('clf', MultinomialNB())
        ])
        self.is_trained = False
        self._train_initial_model()
        
    def _train_initial_model(self):
        # We bootstrap the ML model with some synthetic data to simulate a pre-trained classifier
        X = [
            "WALMART STORE", "TARGET", "WHOLE FOODS", "KROGER", "SAFEWAY",
            "MCDONALDS", "STARBUCKS", "CHIPOTLE", "SUBWAY", "TACO BELL",
            "AMAZON", "EBAY", "ETSY", "ALIEXPRESS",
            "BEST BUY", "APPLE STORE", "SAMSUNG", "MICROCENTER",
            "SHELL", "CHEVRON", "EXXON", "BP",
            "BINANCE", "COINBASE", "KRAKEN", "GEMINI", "CRYPTO COM",
            "DRAFTKINGS", "FANDUEL", "BETMGM", "CAESARS", "BOVADA"
        ]
        y = [
            "retail", "retail", "retail", "retail", "retail",
            "food_and_dining", "food_and_dining", "food_and_dining", "food_and_dining", "food_and_dining",
            "retail", "retail", "retail", "retail",
            "electronics", "electronics", "electronics", "electronics",
            "auto_and_transport", "auto_and_transport", "auto_and_transport", "auto_and_transport",
            "crypto", "crypto", "crypto", "crypto", "crypto",
            "gambling", "gambling", "gambling", "gambling", "gambling"
        ]
        self.model.fit(X, y)
        self.is_trained = True
        
    def predict(self, normalized_text: str) -> Tuple[str, float]:
        if not self.is_trained or not normalized_text:
            return ("unknown", 1.0)
        
        probs = self.model.predict_proba([normalized_text])[0]
        max_idx = np.argmax(probs)
        conf = float(probs[max_idx])
        category = self.model.classes_[max_idx]
        return (category, conf)

ml_engine = CategorizationML()

def categorize_merchant(merchant: str) -> Tuple[str, float, str]:
    """Returns (category, confidence, source)"""
    if not merchant:
        return ("unknown", 1.0, "lookup")
        
    normalized = normalize_merchant(merchant)
    
    # Stage 1: Exact Lookup
    for key, cat in LOOKUP_TABLE.items():
        if key in normalized:
            return (cat, 1.0, "lookup")
            
    # Stage 2: ML Classifier
    category, confidence = ml_engine.predict(normalized)
    return (category, confidence, "ml")
