# !pip install tabpfn torch pandas scikit-learn

import pandas as pd
import os
import torch
import warnings
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from tabpfn import TabPFNClassifier
from tabpfn.constants import ModelVersion

# 1. Address the PyTorch Warning
os.environ["PYTORCH_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TABPFN_ALLOW_CPU_LARGE_DATASET"] = "1"
warnings.filterwarnings("ignore", category=UserWarning)

def preprocess_features(X):
    """Lowercase all string/bool columns."""
    X = X.copy()
    cols_to_fix = X.select_dtypes(include=['object', 'bool']).columns
    for col in cols_to_fix:
        X[col] = X[col].astype(str).str.lower()
    return X

def run_tabpfn_pipeline(data_path, target_col, threshold=0.5):
    """
    Loads data, preprocesses, trains TabPFN, and evaluates with a manual threshold.
    """
    # 1. Check for file existence
    if not os.path.exists(data_path):
        print(f"ERROR: The file '{data_path}' was not found.")
        return

    # 2. Load and Basic Clean
    df = pd.read_csv(data_path)
    print(f"Data successfully loaded. Total rows: {len(df)}")

    # Separate features and target
    X = df.drop(columns=[target_col])
    y = df[target_col].map({"N": 0, "Y": 1})
    
    print(f"Features: {X.shape[1]} columns, Target: {y.value_counts().to_dict()}")

    # 3. Split Data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Initialize Device and Model
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    clf = TabPFNClassifier.create_default_for_version(
        ModelVersion.V2,
        device=device,
        ignore_pretraining_limits=True
    )

    # 5. Create Pipeline with preprocessing + model
    pipeline = Pipeline([
        ('preprocessor', FunctionTransformer(preprocess_features, validate=False)),
        ('classifier', clf)
    ])
    
    print("Training pipeline (preprocessing + TabPFN)...")
    pipeline.fit(X_train, y_train)
    
    # Get probabilities for the positive class (1)
    y_prob = pipeline.predict_proba(X_test)[:, 1]
    
    # Apply manual threshold
    y_pred = (y_prob >= threshold).astype(int)

    # 6. Evaluation Metrics
    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print("\n" + "="*30)
    print(f"RESULTS (Threshold: {threshold})")
    print("="*30)
    print(f"Accuracy: {acc:.4f}")
    print(f"ROC-AUC:  {auc:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"TP (Correct Fraud)     : {tp}")
    print(f"FP (False Alarm)       : {fp}")
    print(f"FN (Missed Fraud)      : {fn}")
    print(f"TN (Correct Non-Fraud) : {tn}")
    print("="*30)

    return pipeline

# --- EXECUTION ---
DATA_PATH = "../all_three_provider_3k_dt_new.csv"
TARGET_COLUMN = "farc_label"
MODEL_OUTPUT_PATH = "sagemaker/tabpfn_classifier.tabpfn_fit"

# Run the function
pipeline = run_tabpfn_pipeline(DATA_PATH, TARGET_COLUMN, threshold=0.5)

# Save fitted model
from tabpfn.model_loading import save_fitted_tabpfn_model

save_fitted_tabpfn_model(pipeline.named_steps['classifier'], MODEL_OUTPUT_PATH)
print(f"\nModel saved: '{MODEL_OUTPUT_PATH}'")

