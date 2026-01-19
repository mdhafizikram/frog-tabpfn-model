# Inference Execution Flow

## Complete Request Flow (Step-by-Step)

### 1. Client Makes Request
```bash
curl -X POST https://api-gateway-url/predict \
  -H "Content-Type: application/json" \
  -d '{"data": [{"nameRiskLevel": "medium", ...}]}'
```

---

### 2. API Gateway → Lambda Invoker

**File**: `src/lambda/invoker.ts`

```typescript
export const handler: APIGatewayProxyHandlerV2 = async (event) => {
  // 1. Parse incoming request
  const body = event.body;  // Your JSON data
  
  // 2. Create SageMaker invocation command
  const command = new InvokeEndpointCommand({
    EndpointName: ENDPOINT_NAME,
    ContentType: "application/json",
    Body: new TextEncoder().encode(body),
  });
  
  // 3. Call SageMaker endpoint
  const response = await client.send(command);
  
  // 4. Return response to client
  return {
    statusCode: 200,
    body: new TextDecoder().decode(response.Body)
  };
}
```

**What happens:**
- ✅ Receives HTTP POST from API Gateway
- ✅ Extracts JSON body
- ✅ Forwards to SageMaker endpoint
- ✅ Returns SageMaker response to client

**Timeout**: 300 seconds

---

### 3. SageMaker Endpoint → Docker Container

**Container Entry Point** (from Dockerfile):
```dockerfile
ENTRYPOINT ["python", "-m", "sagemaker_inference", "serve"]
```

**What happens:**
- ✅ SageMaker's built-in model server starts
- ✅ Listens on port 8080
- ✅ Exposes two endpoints:
  - `GET /ping` - Health check
  - `POST /invocations` - Inference

---

### 4. SageMaker Model Server → Your Inference Code

**File**: `src/sagemaker/inference.py`

The SageMaker model server calls your functions in this order:

#### **Step 4a: Load Model (Once on Cold Start)**

```python
def model_fn(model_dir):
    """Called ONCE when container starts"""
    model_path = os.path.join(model_dir, "tabpfn_model.pkl")
    logger.info(f"Loading model from {model_path}")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    
    model = joblib.load(model_path)  # Loads sklearn Pipeline
    logger.info("Model loaded successfully")
    return model
```

**When**: Container startup (cold start)  
**Input**: `/opt/ml/model/` directory path  
**Output**: Loaded model (sklearn Pipeline with preprocessing + TabPFN)  
**Duration**: 30-60 seconds (loads 500MB+ transformer weights)

---

#### **Step 4b: Deserialize Input (Every Request)**

```python
def input_fn(request_body, request_content_type):
    """Called for EVERY request - deserializes JSON"""
    if request_content_type == "application/json":
        input_data = json.loads(request_body)
        data = input_data.get("data", input_data)
        if isinstance(data, dict):
            data = [data]  # Convert single dict to list
        return data
    raise ValueError(f"Unsupported content type: {request_content_type}")
```

**When**: Every inference request  
**Input**: Raw JSON string from Lambda  
**Output**: Python list of dictionaries  
**Example**:
```python
# Input (JSON string):
'{"data": [{"nameRiskLevel": "medium", "phoneLevel": "high"}]}'

# Output (Python list):
[{"nameRiskLevel": "medium", "phoneLevel": "high"}]
```

---

#### **Step 4c: Run Prediction (Every Request)**

```python
def predict_fn(input_data, model):
    """Called for EVERY request - runs inference"""
    logger.info(f"Running inference on {len(input_data)} samples")
    df = pd.DataFrame(input_data)
    
    # Pipeline handles preprocessing automatically!
    # No manual lowercase/preprocessing needed
    predictions = model.predict(df).tolist()
    probabilities = model.predict_proba(df)[:, 1].tolist()
    
    logger.info(f"Inference complete: {len(predictions)} predictions")
    return {"predictions": predictions, "probabilities": probabilities}
```

**When**: Every inference request  
**Input**: 
- `input_data`: List of dicts from `input_fn()`
- `model`: sklearn Pipeline from `model_fn()`

**What happens internally:**
1. Convert to pandas DataFrame
2. **Pipeline Step 1**: `FunctionTransformer` applies `preprocess_features()` (lowercase strings)
3. **Pipeline Step 2**: `TabPFNClassifier` runs inference on GPU
4. Return predictions + probabilities

**Output**: 
```python
{
  "predictions": [0, 1, 0],  # Binary: 0=no fraud, 1=fraud
  "probabilities": [0.123, 0.876, 0.234]  # Fraud probability
}
```

**Duration**: 100-200ms (warm inference)

---

#### **Step 4d: Serialize Output (Every Request)**

```python
def output_fn(prediction, accept):
    """Called for EVERY request - serializes response"""
    return json.dumps(prediction), "application/json"
```

**When**: Every inference request  
**Input**: Dict from `predict_fn()`  
**Output**: JSON string  

---

### 5. Response Flow Back to Client

```
SageMaker Container
  ↓ (JSON response)
Lambda Invoker
  ↓ (HTTP 200 + JSON body)
API Gateway
  ↓ (HTTP response)
Client
```

---

## Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ CLIENT                                                          │
│ curl -X POST /predict -d '{"data": [...]}'                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ API GATEWAY (AWS)                                               │
│ Routes: POST /predict → Lambda                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAMBDA INVOKER (src/lambda/invoker.ts)                          │
│ - Receives HTTP request                                         │
│ - Calls SageMaker InvokeEndpoint API                            │
│ - Returns response                                              │
│ Timeout: 300s                                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ SAGEMAKER ENDPOINT (ml.g4dn.xlarge GPU)                         │
│ - Receives JSON payload                                         │
│ - Routes to Docker container                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ DOCKER CONTAINER (ECR)                                          │
│ Entry: python -m sagemaker_inference serve                      │
│ - Starts model server on port 8080                             │
│ - Exposes /ping and /invocations                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ SAGEMAKER MODEL SERVER (Built-in)                               │
│ POST /invocations → Calls your inference.py functions           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ YOUR INFERENCE CODE (src/sagemaker/inference.py)                │
│                                                                 │
│ COLD START (First Request):                                    │
│   1. model_fn(model_dir)                                        │
│      - Load tabpfn_model.pkl (sklearn Pipeline)                │
│      - Initialize CUDA                                          │
│      - Duration: 30-60 seconds                                  │
│                                                                 │
│ EVERY REQUEST:                                                  │
│   2. input_fn(request_body, content_type)                       │
│      - Parse JSON → Python list                                 │
│                                                                 │
│   3. predict_fn(input_data, model)                              │
│      - Convert to DataFrame                                     │
│      - Pipeline Step 1: preprocess_features() (lowercase)       │
│      - Pipeline Step 2: TabPFNClassifier.predict()             │
│      - Return predictions + probabilities                       │
│      - Duration: 100-200ms                                      │
│                                                                 │
│   4. output_fn(prediction, accept)                              │
│      - Serialize to JSON                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE BACK TO CLIENT                                         │
│ {"predictions": [0], "probabilities": [0.123]}                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Function Call Order

### Cold Start (First Request After Deployment)
```
1. Container starts
2. model_fn()           ← Load model (30-60s)
3. input_fn()           ← Parse request
4. predict_fn()         ← Run inference (100-200ms)
5. output_fn()          ← Serialize response
Total: ~60-90 seconds
```

### Warm Requests (Subsequent Requests)
```
1. input_fn()           ← Parse request
2. predict_fn()         ← Run inference (100-200ms)
3. output_fn()          ← Serialize response
Total: ~100-200ms
```

---

## Key Points

1. **model_fn() runs ONCE** - Model stays in memory between requests
2. **input_fn(), predict_fn(), output_fn() run EVERY request**
3. **Pipeline handles preprocessing automatically** - No manual code in predict_fn()
4. **GPU acceleration** - TabPFN uses CUDA if available
5. **Timeout chain**: Client → API Gateway (30s) → Lambda (300s) → SageMaker (3600s)

---

## Logging

Check CloudWatch logs to see function execution:

```bash
aws logs tail /aws/sagemaker/Endpoints/<endpoint-name> --follow --profile asu-frog-sandbox
```

You'll see:
```
Loading model from /opt/ml/model/tabpfn_model.pkl
CUDA available: True
CUDA device: Tesla T4
Model loaded successfully
Running inference on 1 samples
Inference complete: 1 predictions
```

---

## Performance Breakdown

| Stage | Duration | Frequency |
|-------|----------|-----------|
| API Gateway | <10ms | Every request |
| Lambda invocation | 10-50ms | Every request |
| SageMaker routing | 10-20ms | Every request |
| model_fn() | 30-60s | Cold start only |
| input_fn() | <1ms | Every request |
| predict_fn() | 100-200ms | Every request |
| output_fn() | <1ms | Every request |
| **Total (cold)** | **60-90s** | First request |
| **Total (warm)** | **100-300ms** | Subsequent requests |
