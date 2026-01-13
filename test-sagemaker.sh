#!/bin/bash
set -e

echo "=== TabPFN SageMaker Docker Test ==="
echo ""

# Clean up any existing containers
echo "Cleaning up..."
docker stop tabpfn-sagemaker 2>/dev/null || true
docker rm tabpfn-sagemaker 2>/dev/null || true

# Build SageMaker image
echo "Building SageMaker Docker image..."
cd src
docker build -t tabpfn-fraud:sagemaker .
cd ..

# Run container (simulating SageMaker environment)
echo "Starting container..."
docker run -d --name tabpfn-sagemaker \
  -p 8080:8080 \
  -e MODEL_PATH=/opt/ml/model/tabpfn_model.pkl \
  tabpfn-fraud:sagemaker

echo "Waiting for model to load (30 seconds for TabPFN)..."
sleep 30

# Test health (SageMaker uses /ping)
echo -e "\n=== Testing /ping Endpoint ==="
curl -s --max-time 10 http://localhost:8080/ping || echo "Ping failed"

# Test prediction (SageMaker uses /invocations)
echo -e "\n\n=== Testing /invocations Endpoint (may take 1-2 min on CPU) ==="
curl -s --max-time 300 -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d @test-request.json || echo "Invocation failed"

echo -e "\n\n=== Container Logs ==="
docker logs tabpfn-sagemaker --tail 30

echo -e "\n\n=== Summary ==="
echo "Docker image: tabpfn-fraud:sagemaker"
echo ""
echo "Commands:"
echo "  View logs:    docker logs tabpfn-sagemaker"
echo "  Stop:         docker stop tabpfn-sagemaker && docker rm tabpfn-sagemaker"
echo ""
echo "To deploy to AWS SageMaker:"
echo "  pnpm install"
echo "  pnpm run deploy"
