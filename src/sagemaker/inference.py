"""
SageMaker inference script for TabPFN model.
Uses the model_fn, input_fn, predict_fn, output_fn interface.
"""
import os
import sys
import json
import logging
import joblib
import pandas as pd
import torch
import warnings

# Add current directory to path for preprocessing module
sys.path.insert(0, os.path.dirname(__file__))
from preprocessing import preprocess_features

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TABPFN_ALLOW_CPU_LARGE_DATASET"] = "1"


def model_fn(model_dir):
    """Load fitted TabPFN model (required by SageMaker)."""
    from tabpfn.model_loading import load_fitted_tabpfn_model
    
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA device count: {torch.cuda.device_count()}")
        logger.info(f"CUDA device name: {torch.cuda.get_device_name(0)}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading model on device: {device}")
    
    classifier = load_fitted_tabpfn_model(
        os.path.join(model_dir, "tabpfn_classifier.tabpfn_fit"), 
        device=device
    )
    
    logger.info("Model loaded successfully")
    return classifier


def input_fn(request_body, request_content_type):
    """Deserialize input data (required by SageMaker)."""
    if request_content_type == "application/json":
        input_data = json.loads(request_body)
        data = input_data.get("data", input_data)
        if isinstance(data, dict):
            data = [data]
        return data
    raise ValueError(f"Unsupported content type: {request_content_type}")


def predict_fn(input_data, model):
    """Run prediction using fitted model (required by SageMaker)."""
    import time
    logger.info(f"Prediction started for {len(input_data)} records")
    start = time.time()
    
    df = pd.DataFrame(input_data)
    X_processed = preprocess_features(df)
    predictions = model.predict(X_processed).tolist()
    probabilities = model.predict_proba(X_processed)[:, 1].tolist()
    
    logger.info(f"Prediction completed in {time.time() - start:.2f}s")
    return {"predictions": predictions, "probabilities": probabilities}


def output_fn(prediction, accept):
    """Serialize output (required by SageMaker)."""
    return json.dumps(prediction), "application/json"
