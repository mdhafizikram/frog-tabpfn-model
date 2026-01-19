"""
Shared preprocessing functions for TabPFN model.
"""

def preprocess_features(X):
    """Lowercase all string/bool columns."""
    X = X.copy()
    cols_to_fix = X.select_dtypes(include=['object', 'bool']).columns
    for col in cols_to_fix:
        X[col] = X[col].astype(str).str.lower()
    return X
