import joblib
import pandas as pd
import sys

if len(sys.argv) < 2:
    print("Usage: python3 load_model.py <new_data.csv>")
    sys.exit(1)

model = joblib.load("tabpfn_model.pkl")
new_data = pd.read_csv(sys.argv[1])

# Preprocess: lowercase string/bool columns
cols_to_fix = new_data.select_dtypes(include=['object', 'bool']).columns
for col in cols_to_fix:
    new_data[col] = new_data[col].astype(str).str.lower()

predictions = model.predict(new_data)
probabilities = model.predict_proba(new_data)[:, 1]

results = pd.DataFrame({
    'prediction': predictions,
    'probability': probabilities
})

results.to_csv('predictions.csv', index=False)
print(f"Predictions saved to 'predictions.csv'")
print(f"Total samples: {len(predictions)}")
print(f"Predicted fraud: {sum(predictions)}")
print(f"Predicted non-fraud: {len(predictions) - sum(predictions)}")
