#!/usr/bin/env python3
"""
SageMaker inference server for TabPFN model.
Implements /ping and /invocations endpoints required by SageMaker.
"""
import os
import json
import logging
import joblib
import pandas as pd
import torch
from flask import Flask, request, Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment setup for TabPFN
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TABPFN_ALLOW_CPU_LARGE_DATASET"] = "1"

app = Flask(__name__)

# Global model variable
model = None

def load_model():
    """Load the TabPFN model from the model directory."""
    global model
    model_path = os.environ.get("MODEL_PATH", "/opt/ml/model/tabpfn_model.pkl")
    
    logger.info(f"Loading model from {model_path}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
    
    model = joblib.load(model_path)
    logger.info("Model loaded successfully")
    return model

@app.route("/ping", methods=["GET"])
def ping():
    """Health check endpoint required by SageMaker."""
    health = model is not None
    status = 200 if health else 404
    return Response(
        response=json.dumps({"status": "healthy" if health else "unhealthy"}),
        status=status,
        mimetype="application/json"
    )

@app.route("/invocations", methods=["POST"])
def invocations():
    """Inference endpoint required by SageMaker."""
    if model is None:
        return Response(
            response=json.dumps({"error": "Model not loaded"}),
            status=503,
            mimetype="application/json"
        )
    
    try:
        content_type = request.content_type
        
        if content_type == "application/json":
            input_data = request.get_json()
            data = input_data.get("data", input_data)
            if isinstance(data, dict):
                data = [data]
        else:
            return Response(
                response=json.dumps({"error": f"Unsupported content type: {content_type}"}),
                status=415,
                mimetype="application/json"
            )
        
        df = pd.DataFrame(data)
        
        # Preprocess: lowercase string/bool columns
        cols_to_fix = df.select_dtypes(include=['object', 'bool']).columns
        for col in cols_to_fix:
            df[col] = df[col].astype(str).str.lower()
        
        logger.info(f"Running inference on {len(df)} samples")
        
        # Run prediction
        predictions = model.predict(df).tolist()
        probabilities = model.predict_proba(df)[:, 1].tolist()
        
        result = {
            "predictions": predictions,
            "probabilities": probabilities
        }
        
        logger.info(f"Inference complete: {len(predictions)} predictions")
        
        return Response(
            response=json.dumps(result),
            status=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"Inference error: {str(e)}")
        return Response(
            response=json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json"
        )

if __name__ == "__main__":
    load_model()
    app.run(host="0.0.0.0", port=8080)
