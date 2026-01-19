# Quick Start Guide

## Complete Deployment in 4 Steps

### 1️⃣ Train Model with Pipeline
```bash
cd src
pip install tabpfn pandas scikit-learn
python3 tabpfn_model_test.py
cd ..
```

**What this does:**
- Trains TabPFN on fraud data (from `../all_three_provider_3k_dt_new.csv`)
- Bundles preprocessing + model in sklearn Pipeline
- Saves to `src/tabpfn_model.pkl`

---

### 2️⃣ Build & Push Docker Image
```bash
./build-and-push.sh
```

**What this does:**
- Builds optimized Docker image (PyTorch + TabPFN)
- Creates ECR repository
- Pushes image to AWS ECR
- Outputs image URI

**Copy the image URI from output!**

---

### 3️⃣ Configure Environment
```bash
# Edit .env file and add:
DOCKER_IMAGE_URI=<paste-image-uri-here>
```

---

### 4️⃣ Deploy to AWS
```bash
pnpm install
pnpm deploy
```

**What this does:**
- Creates S3 bucket for model
- Uploads model.tar.gz
- Deploys SageMaker endpoint (5-10 min)
- Creates Lambda + API Gateway

**Wait for deployment to complete, then copy API URL from output.**

---

## Test Your Deployment

```bash
# Wait 60-90 seconds for cold start, then:
curl -X POST <your-api-url>/predict \
  -H "Content-Type: application/json" \
  -d @test-request.json
```

**Expected response:**
```json
{
  "predictions": [0],
  "probabilities": [0.123]
}
```

---

## Cleanup (Stop Billing)

```bash
pnpm remove
```

This deletes the SageMaker endpoint to stop hourly charges.

---

## Troubleshooting

### "DOCKER_IMAGE_URI not set"
- Run `./build-and-push.sh` first
- Add URI to `.env` file

### First request times out
- Wait 60-90 seconds after deployment
- SageMaker needs time for cold start (model loading + CUDA init)

### Docker build fails
- Check Docker daemon is running: `docker ps`
- Ensure 10GB+ free disk space

### Deployment fails
- Check AWS credentials: `aws sts get-caller-identity --profile asu-frog-sandbox`
- Verify region is `us-west-2`

---

## Architecture

```
Client
  ↓
API Gateway
  ↓
Lambda (300s timeout)
  ↓
SageMaker Endpoint (ml.g4dn.xlarge GPU)
  ↓
Custom Docker Container (ECR)
  ├── PyTorch 2.1.0 + CUDA 11.8
  ├── TabPFN 6.3.0
  └── sklearn Pipeline (preprocessing + model)
  ↓
Predictions
```

---

## Cost

- **Dev**: ~$0.73/hour (ml.g4dn.xlarge)
- **Prod**: ~$1.41/hour (ml.g5.xlarge)
- **Lambda**: ~$0.20 per 1M requests
- **API Gateway**: ~$1.00 per 1M requests

**Remember to run `pnpm remove` when not in use!**

---

## Files Reference

- `DEPLOY.md` - Detailed deployment guide
- `PIPELINE_CHANGES.md` - Pipeline implementation details
- `CHANGES.md` - Summary of all fixes
- `test-request.json` - Sample inference request
