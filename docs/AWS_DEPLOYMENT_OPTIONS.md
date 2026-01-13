# AWS Deployment Options for TabPFN PKL Model

## Ranked by Efficiency (Cost + Performance + Simplicity)

---

## 🥇 #1: ECS Fargate with Application Load Balancer

**Best for: Production workloads with moderate traffic**

### Setup
```
FastAPI/Flask → Docker Container → ECS Fargate → ALB → API Gateway (optional)
```

### Specs
- **Instance**: 2 vCPU, 4GB RAM
- **Cost**: ~$43/month (24/7) or ~$0.06/hour
- **Cold start**: 10-30 seconds (first request)
- **Inference**: 2-5 seconds per 100 records

### Pros
✓ Serverless (no server management)
✓ Auto-scaling built-in
✓ Pay only for what you use
✓ Easy CI/CD integration
✓ Load balancing included

### Cons
✗ Cold starts on scale-down
✗ CPU-only (slower inference)

### When to Use
- 100-10,000 requests/day
- Can tolerate 2-5 second latency
- Want minimal ops overhead

**Efficiency Score: 9/10**

---

## 🥈 #2: SageMaker Serverless Inference

**Best for: Unpredictable/sporadic traffic**

### Setup
```
PKL → SageMaker Model → Serverless Endpoint → API Gateway
```

### Specs
- **Memory**: 4GB
- **Cost**: $0.20 per 1000 invocations + compute time
- **Cold start**: 10-60 seconds
- **Inference**: 2-5 seconds per 100 records

### Pros
✓ True pay-per-use (no idle costs)
✓ Auto-scaling to zero
✓ Managed infrastructure
✓ Built-in monitoring

### Cons
✗ Cold starts frequent
✗ Higher per-request cost at scale
✗ 60-second timeout limit

### When to Use
- <1,000 requests/day
- Sporadic/unpredictable traffic
- Cost optimization priority

**Efficiency Score: 8/10**

---

## 🥉 #3: EC2 with Auto Scaling

**Best for: High-volume, predictable traffic**

### Setup
```
FastAPI → EC2 (t3.xlarge) → Auto Scaling Group → ALB
```

### Specs
- **Instance**: t3.xlarge (4 vCPU, 16GB RAM)
- **Cost**: ~$122/month (24/7) or $0.17/hour
- **Cold start**: None (always warm)
- **Inference**: 2-5 seconds per 100 records

### Pros
✓ No cold starts
✓ Full control
✓ Predictable performance
✓ Can use Spot instances (60% savings)

### Cons
✗ Manual infrastructure management
✗ Pay for idle time
✗ More complex setup

### When to Use
- >10,000 requests/day
- Need consistent low latency
- Have DevOps resources

**Efficiency Score: 7/10**

---

## 🏆 #4: ECS Fargate with GPU (BEST PERFORMANCE)

**Best for: High-volume + need speed**

### Setup
```
FastAPI → Docker → ECS Fargate (GPU) → ALB
```

### Specs
- **Instance**: 4 vCPU, 8GB RAM, 1 GPU
- **Cost**: ~$200-300/month
- **Cold start**: 15-45 seconds
- **Inference**: 0.2-0.5 seconds per 100 records (10x faster!)

### Pros
✓ 10x faster inference
✓ Serverless GPU
✓ Auto-scaling
✓ Handle high throughput

### Cons
✗ Higher cost
✗ GPU availability limits
✗ Longer cold starts

### When to Use
- Need sub-second latency
- High request volume
- Real-time requirements

**Efficiency Score: 8/10** (if speed matters)

---

## ❌ NOT RECOMMENDED: Lambda

### Why Not
- Package size: 3GB (exceeds 250MB limit)
- Cold start: 30+ seconds
- Memory: Need 3-4GB minimum
- Timeout: Inference may exceed 15min limit

**Efficiency Score: 2/10** (technically possible with layers/EFS, but painful)

---

## Cost Comparison (Monthly, 24/7)

| Option | Cost | Latency | Scalability | Ops Overhead |
|--------|------|---------|-------------|--------------|
| ECS Fargate (CPU) | $43 | Medium | High | Low |
| SageMaker Serverless | $20-200* | Medium-High | High | Very Low |
| EC2 Auto Scaling | $122 | Low | Medium | Medium |
| ECS Fargate (GPU) | $250 | Very Low | High | Low |
| Lambda | N/A | High | High | Low |

*Depends on request volume

---

## Recommended Architecture

### For Your Fraud Detection Use Case:

```
┌─────────────┐
│ API Gateway │ ← REST API endpoint
└──────┬──────┘
       │
┌──────▼──────────┐
│ ECS Fargate     │ ← FastAPI container
│ 2 vCPU, 4GB RAM │ ← Load model on startup
└──────┬──────────┘
       │
┌──────▼──────┐
│ S3 Bucket   │ ← Store tabpfn_model.pkl
└─────────────┘
```

### Implementation Steps:

1. **Create FastAPI app** (inference endpoint)
2. **Dockerize** with PyTorch + TabPFN
3. **Upload PKL to S3**
4. **Deploy to ECS Fargate**
5. **Add ALB for load balancing**
6. **Configure auto-scaling** (CPU > 70%)

---

## Quick Start: Minimal Deployment

### Option A: ECS Fargate (Recommended)
```bash
# 1. Create Dockerfile
# 2. Build and push to ECR
# 3. Create ECS task definition
# 4. Deploy to Fargate
# 5. Expose via ALB

Estimated setup time: 2-4 hours
Monthly cost: $43-60
```

### Option B: SageMaker Serverless (Easiest)
```bash
# 1. Create inference.py script
# 2. Package with requirements.txt
# 3. Upload to S3
# 4. Create SageMaker model
# 5. Deploy serverless endpoint

Estimated setup time: 1-2 hours
Monthly cost: $20-100 (usage-based)
```

---

## Performance Optimization Tips

1. **Model Caching**: Load PKL once at startup, reuse for all requests
2. **Batch Inference**: Process multiple records together
3. **Connection Pooling**: Reuse HTTP connections
4. **Async Processing**: Use queues (SQS) for non-real-time
5. **Monitoring**: CloudWatch for latency/error tracking

---

## Final Recommendation

### Start with: **ECS Fargate (CPU)**
- Best cost/performance balance
- Easy to set up and maintain
- Scales automatically
- ~$43/month for 24/7 availability

### Upgrade to: **ECS Fargate (GPU)** if:
- Request volume > 10,000/day
- Need sub-second latency
- Budget allows $250+/month

### Use: **SageMaker Serverless** if:
- Very low/sporadic traffic
- Want absolute minimal cost
- Can tolerate cold starts

---

## Next Steps

1. Create FastAPI inference endpoint
2. Dockerize the application
3. Set up ECS Fargate deployment
4. Configure monitoring and alerts
5. Test with production traffic

Would you like me to create the deployment code for any of these options?
