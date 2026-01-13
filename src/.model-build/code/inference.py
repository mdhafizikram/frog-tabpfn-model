"""
SageMaker inference script for TabPFN model.
Uses the model_fn, input_fn, predict_fn, output_fn interface.
"""
import os
import json
import logging
import joblib
import pandas as pd
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TABPFN_ALLOW_CPU_LARGE_DATASET"] = "1"


def model_fn(model_dir):
    """Load model from the model_dir (required by SageMaker)."""
    model_path = os.path.join(model_dir, "tabpfn_model.pkl")
    logger.info(f"Loading model from {model_path}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
    model = joblib.load(model_path)
    logger.info("Model loaded successfully")
    return model


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
    """Run prediction (required by SageMaker)."""
    df = pd.DataFrame(input_data)
    
    cols_to_fix = df.select_dtypes(include=['object', 'bool']).columns
    for col in cols_to_fix:
        df[col] = df[col].astype(str).str.lower()
    
    logger.info(f"Running inference on {len(df)} samples")
    
    predictions = model.predict(df).tolist()
    probabilities = model.predict_proba(df)[:, 1].tolist()
    
    return {"predictions": predictions, "probabilities": probabilities}


def output_fn(prediction, accept):
    """Serialize output (required by SageMaker)."""
    return json.dumps(prediction), "application/json"
