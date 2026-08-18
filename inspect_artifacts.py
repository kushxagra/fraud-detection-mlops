import joblib

model = joblib.load('xgb_fraud_model.pkl')
scaler = joblib.load('robust_scaler.pkl')

print("Scaler expects this many features:", scaler.n_features_in_)
print("Model expects this many features:", model.n_features_in_)

# If the model is an XGBClassifier, this often reveals the exact column
# names/order it was trained on:
try:
    print("Model's known feature names:", model.get_booster().feature_names)
except Exception as e:
    print("Could not read feature names:", e)