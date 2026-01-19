# Optimized SageMaker container for TabPFN inference
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/ml

# Copy and install Python dependencies
COPY requirements.txt /opt/ml/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy inference code
COPY inference.py /opt/ml/code/inference.py
COPY serve.py /opt/ml/code/serve.py
COPY preprocessing.py /opt/ml/code/preprocessing.py
RUN touch /opt/ml/code/__init__.py

# Environment variables for TabPFN
ENV PYTHONUNBUFFERED=TRUE \
    PYTHONDONTWRITEBYTECODE=TRUE \
    PYTHONWARNINGS=ignore::DeprecationWarning \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
    TABPFN_ALLOW_CPU_LARGE_DATASET=1 \
    SM_MODEL_DIR=/opt/ml/model \
    PYTHONPATH=/opt/ml/code

# SageMaker uses port 8080
EXPOSE 8080

# Health check
HEALTHCHECK CMD curl -f http://localhost:8080/ping || exit 1

# Use gunicorn to serve the Flask app
WORKDIR /opt/ml/code
ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8080", "-w", "1", "--timeout", "900", "--graceful-timeout", "900", "serve:app"]
