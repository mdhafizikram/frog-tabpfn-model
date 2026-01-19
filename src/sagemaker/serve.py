#!/usr/bin/env python3
"""
Simple Flask server for SageMaker inference.
"""
import os
import json
import logging
import threading
from flask import Flask, request, jsonify
import inference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Model will be loaded on first request
model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")
model = None
model_lock = threading.Lock()

def get_model():
    """Lazy load model on first request (thread-safe)"""
    global model
    if model is None:
        with model_lock:
            if model is None:  # Double-check after acquiring lock
                logger.info(f"Loading model from {model_dir}...")
                model = inference.model_fn(model_dir)
                logger.info("Model loaded successfully")
    return model

@app.route("/ping", methods=["GET"])
def ping():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route("/invocations", methods=["POST"])
def invocations():
    """Inference endpoint"""
    try:
        current_model = get_model()
        content_type = request.content_type or "application/json"
        request_body = request.data.decode('utf-8') if isinstance(request.data, bytes) else request.data
        input_data = inference.input_fn(request_body, content_type)
        prediction = inference.predict_fn(input_data, current_model)
        response_body, response_type = inference.output_fn(prediction, "application/json")
        return response_body, 200, {"Content-Type": response_type}
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
