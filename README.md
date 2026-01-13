# TabPFN Fraud Detection Model

TabPFN model for fraud detection with 95.9% accuracy and 98.5% ROC-AUC.

## Project Structure

```
.
├── src/                    # Python application code
│   ├── app.py             # FastAPI inference API
│   ├── tabpfn_model_test.py  # Training script
│   ├── load_model.py      # CLI inference
│   ├── Dockerfile         # Container definition
│   └── requirements.txt   # Python dependencies
├── docs/                  # Documentation
│   ├── USE_CASE.md
│   ├── AWS_DEPLOYMENT_OPTIONS.md
│   ├── MODEL_FORMAT_COMPARISON.md
│   └── DEPLOYMENT.md
├── sst.config.ts          # AWS infrastructure (SST v3)
├── package.json           # Node.js dependencies
├── tabpfn_model.pkl       # Trained model
└── all_three_provider_3k_dt_new.csv  # Training data
```

## Quick Start

### 1. Train Model
```bash
cd src
pip install -r requirements.txt
python3 tabpfn_model_test.py
```

### 2. Test Locally
```bash
cd src
uvicorn app:app --reload
```

### 3. Deploy to AWS
```bash
npm install
npm run deploy
```

## Documentation

See [docs/](docs/) for detailed documentation:
- [USE_CASE.md](docs/USE_CASE.md) - Business case
- [AWS_DEPLOYMENT_OPTIONS.md](docs/AWS_DEPLOYMENT_OPTIONS.md) - Deployment options
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide