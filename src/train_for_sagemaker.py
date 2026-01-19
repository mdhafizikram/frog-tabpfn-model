"""
Retrain model with proper module references for SageMaker deployment.
"""
import os
import sys
# Add parent directory to path so we can import preprocessing
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import torch
import warnings
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from tabpfn import TabPFNClassifier
from tabpfn.constants import ModelVersion
from preprocessing import preprocess_features

os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TABPFN_ALLOW_CPU_LARGE_DATASET"] = "1"
warnings.filterwarnings("ignore", category=UserWarning)

DATA_PATH = "../all_three_provider_3k_dt_new.csv"
TARGET_COLUMN = "farc_label"

# Load data
df = pd.read_csv(DATA_PATH)
print(f"Data loaded: {len(df)} rows")

X = df.drop(columns=[TARGET_COLUMN])
y = df[TARGET_COLUMN].map({"N": 0, "Y": 1})

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

clf = TabPFNClassifier.create_default_for_version(
    ModelVersion.V2,
    device=device,
    ignore_pretraining_limits=True
)

# Create pipeline - now preprocess_features is from inference module
pipeline = Pipeline([
    ('preprocessor', FunctionTransformer(preprocess_features, validate=False)),
    ('classifier', clf)
])

print("Training pipeline...")
pipeline.fit(X_train, y_train)

y_prob = pipeline.predict_proba(X_test)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)

acc = accuracy_score(y_test, y_pred)
auc = roc_auc_score(y_test, y_prob)

print(f"\nAccuracy: {acc:.4f}")
print(f"ROC-AUC:  {auc:.4f}")

# Save model
joblib.dump(pipeline, "tabpfn_model.pkl")
print("\nModel saved as 'tabpfn_model.pkl'")
