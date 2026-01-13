# SageMaker-compatible container for TabPFN model with GPU support
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /opt/program

# Copy requirements and install Python dependencies
COPY requirements.txt /opt/program/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy model and inference code
COPY tabpfn_model.pkl /opt/ml/model/tabpfn_model.pkl
COPY sagemaker/ /opt/program/

# Make serve script executable
RUN chmod +x /opt/program/serve

# Environment variables
ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"
ENV MODEL_PATH=/opt/ml/model/tabpfn_model.pkl

# SageMaker requires port 8080
EXPOSE 8080

# Entry point for SageMaker
ENTRYPOINT ["python", "/opt/program/serve.py"]
