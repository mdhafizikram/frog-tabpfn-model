# SST v3 Deployment Guide

## Prerequisites

1. **Install Node.js** (v18+)
2. **Install SST CLI**
   ```bash
   npm install
   ```
3. **Configure AWS credentials**
   ```bash
   aws configure
   ```

## Deploy to AWS

### 1. Deploy to Development
```bash
npm run dev
```

### 2. Deploy to Production
```bash
npm run deploy --stage production
```

### 3. Remove Stack
```bash
npm run remove
```

## What Gets Deployed

- **ECS Fargate Cluster** - Runs your containerized API
- **Application Load Balancer** - Distributes traffic
- **S3 Bucket** - Stores model artifacts (optional)
- **VPC** - Isolated network with NAT gateway
- **Auto Scaling** - Scales 1-4 instances based on CPU

## Architecture

```
Internet → ALB → ECS Fargate (FastAPI) → TabPFN Model
```

## API Endpoints

### Health Check
```bash
curl https://your-api-url/health
```

### Predict
```bash
curl -X POST https://your-api-url/predict \
  -H "Content-Type: application/json" \
  -d '{
    "data": [
      {"feature1": "value1", "feature2": "value2", ...}
    ]
  }'
```

## Cost Estimate

- **ECS Fargate**: ~$43/month (2 vCPU, 4GB RAM, 24/7)
- **ALB**: ~$16/month
- **NAT Gateway**: ~$32/month
- **Total**: ~$91/month

## Scaling Configuration

- **Min instances**: 1
- **Max instances**: 4
- **Scale trigger**: CPU > 70%

## Monitoring

View logs and metrics:
```bash
sst console
```

Or use AWS Console:
- CloudWatch Logs
- ECS Service metrics
- ALB metrics

## Environment Variables

Set in `sst.config.ts`:
- `MODEL_BUCKET` - S3 bucket for model storage
- `MODEL_KEY` - Model file path in S3

## Troubleshooting

### Container fails to start
```bash
# Check logs
sst logs --stage dev
```

### Model not loading
- Ensure `tabpfn_model.pkl` is in Docker image
- Check file permissions
- Verify memory allocation (4GB minimum)

### Slow inference
- Increase CPU/memory in `sst.config.ts`
- Consider GPU instances (change instance type)
- Implement batch processing
