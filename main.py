import os
import json
import sqlite3
from datetime import datetime
import warnings



warnings.filterwarnings("ignore")



#Third party frameworks for our API and ML pipeline
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, create_model
import joblib
import pandas as pd
import numpy as np 



from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler
from xgboost import XGBClassifier


#initialize the FastAPI app instance
app = FastAPI(
    title = "Production MLOPS Fraud Detection Service",
    description = "Tier 1: High Performance Validation and persistent postgresql analytics storage.",
    version = "1.0.3"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173",
                   "https://fraud-detection-mlops-ashy.vercel.app/",
                   ],  # Vite's default dev server address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#2. Define the PostgreSQL connection string
DB_FILE = "fraud_detections.db"
#3. Create placeholders for our ML artifacts so they are globally accessible
model = None 
scaler = None



fields = {
    "Time":(float, Field(...,ge=0,allow_inf_nan=False,
                         description = "Seconds elapsed since the first transaction")),
    "Amount":(float, Field(...,ge=0,le=1000000,allow_inf_nan=False,description="Transaction amount"))
}



for i in range(1, 29):
    fields[f"V{i}"] = (float, Field(...,ge=-100,le= 100,allow_inf_nan = False,
                        description=f"PCA component V{i}"))




TransactionInput = create_model("TransactionInput",**fields)

PERFORMANCE_THRESHOLDS = {
    "fraud_recall": 0.75,
    "fraud_precision": 0.75,
}

def log_alert(metric_name: str, value: float, threshold: float):
    message = f"{metric_name} dropped to {value} (below threshold {threshold})"
    print(f"[ALERT] {message}")

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO alerts (timestamp, metric_name, value, treshold, message)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().isoformat(), metric_name, value, threshold, message))


def check_performance_and_alert(metrics: dict):
    for metric_name, threshold in PERFORMANCE_THRESHOLDS.items():
        value = metrics.get(metric_name)
        if value is not None and value < threshold:
            log_alert(metric_name, value, threshold)


def init_db():
    """Connect to the local SQLite database and create the prediction log
    table if it doesn't already exist. Raises if this fails -- we want
    startup to fail LOUDLY here rather than limping along with no table."""
    

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_logs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                time_feature REAL,
                amount REAL,
                v1 REAL, v2 REAL, v3 REAL, v4 REAL, v5 REAL, v6 REAL, v7 REAL, v8 REAL, v9 REAL, v10 REAL,
                v11 REAL, v12 REAL, v13 REAL, v14 REAL, v15 REAL, v16 REAL, v17 REAL, v18 REAL, v19 REAL, v20 REAL,
                v21 REAL, v22 REAL, v23 REAL, v24 REAL, v25 REAL, v26 REAL, v27 REAL, v28 REAL,
                prediction INTEGER,
                fraud_probability REAL,
                model_version TEXT
            )
        """)

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS alerts(
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       timestamp TEXT,
                       metric_name TEXT,
                       value REAL,
                       treshold REAL,
                       message TEXT
            )
       """)
    print("[DATABASE] SQLite table ready.")

MODELS_DIR = "models"

MODEL_VERSION = None
MODEL_METADATA = {}

def load_active_model():
    """Reads models/active_version.txt to find which version is 'active'"""
    global model,scaler,MODEL_VERSION, MODEL_METADATA

    pointer_path = os.path.join(MODELS_DIR, "active_version.txt")
    with open(pointer_path, "r") as f:
        version = f.read().strip()

    version_dir = os.path.join(MODELS_DIR, version)

    model = joblib.load(os.path.join(version_dir, "model.pkl"))
    scaler = joblib.load(os.path.join(version_dir, "scaler.pkl"))
    
    metadata_path = os.path.join(version_dir, "metadata.json")
    with open(metadata_path, "r") as f:
        MODEL_METADATA = json.load(f)

    MODEL_VERSION = version
    print(f"[SUCCESS] Loaded active model version: {MODEL_VERSION} with metadata: {MODEL_METADATA}")




@app.on_event("startup")
def startup_event():
    """Triggers automatically when FastAPI starts up."""
    init_db()

    try:
        load_active_model()
        
    except FileNotFoundError as e:
        print(f"[CRITICAL ERROR] ML artifact file not found: {e}")
        model = None
        scaler = None

    except Exception as e:
        print(f"[CRITICAL ERROR] Failed to load ML artifacts: {e}")
        model = None
        scaler = None
    


@app.get("/")
def home():
    return{"message":"Fraud Detection API"}




@app.post("/predict")
def predict(transaction: TransactionInput):
    #predict if transaction is a fraud
    global model, scaler

    if model is None or scaler is None:
        raise HTTPException(status_code = 503, detail="ML model not loaded")
    
    try:
        data = transaction.dict()
        scaled_amount = scaler.transform([[data["Amount"]]])[0][0]
        scaled_time = scaler.transform([[data["Time"]]])[0][0]

        feature_order = [f"V{i}" for i in range(1, 29)] 
        features = [data[f] for f in feature_order]
        features.append(scaled_amount)
        features.append(scaled_time)

        prediction = model.predict([features])[0]
        fraud_probability = model.predict_proba([features])[0][1]
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Model inference failed: {str(e)}")
    # --- Logging (separate from inference -- a logging failure should NOT block the response) ---
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            values = [datetime.now().isoformat(), data["Time"], data["Amount"]]
            for i in range(1, 29):
                values.append(data[f"V{i}"])
            values.extend([int(prediction), float(fraud_probability), "1.0.3"])

            cursor.execute("""
            INSERT INTO prediction_logs 
            (timestamp, time_feature, amount, v1, v2, v3, v4, v5, v6, v7, v8, v9, v10, v11, v12, v13, v14, v15, v16, v17, v18, v19, v20, v21, v22, v23, v24, v25, v26, v27, v28, prediction, fraud_probability, model_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(values))
            # 'with' auto-commits and closes -- no manual conn.commit()/conn.close() needed

    except Exception as e:
        print(f"[DATABASE ERROR] Could not log prediction: {e}")

    # --- Response: always returned, regardless of whether logging succeeded ---
    return {
        "is_fraud": int(prediction),
        "fraud_probability": float(fraud_probability),
        "message": "Fraud Detected" if prediction == 1 else "LEGITIMATE TRANSACTION"
    }
        # Logging is separate from inference -- if THIS fails, still return the prediction.
    


#this model below displays the metrics of the model and the database
@app.get("/metrics")
def get_metrics():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM prediction_logs")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM prediction_logs WHERE prediction = 1")
        fraud_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MAX(timestamp) FROM prediction_logs")
        last_prediction = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()

        return{
            "total_predictions":total,
            "fraud_detected":fraud_count,
            "legitimate":total - fraud_count,
            "fraud_rate": round((fraud_count / total * 100), 2) if total > 0 else 0,
            "last_prediction": last_prediction
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Fetching Metrics: {str(e)}")



#this model below checks for the health of the model(error handler)
@app.get("/health")
def health_check():
    """lightweight health check endpoint to verify API is running and ML artifacts are loaded."""
    db_ok = True

    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("SELECT 1")
        conn.close()
    except Exception as e:
        db_ok = False

    ml_ok = model is not None and scaler is not None

    return{
        "status": "ok" if (db_ok and ml_ok) else "degraded",
        "model_loaded": ml_ok,
        "database_reachable": db_ok
    }


@app.get("/evaluate")
def evaluate_model(sample_size: int = 2000):
    """
    Runs the currently active model against the REAL held-out test set --
    the same one used to compute baseline_metrics during training -- instead
    of the full dataset. Evaluating on training data gives artificially
    perfect scores, since the model has already seen those rows.
    """
    if model is None or scaler is None:
        raise HTTPException(status_code=503, detail="ML model not loaded")

    try:
        df = pd.read_csv("creditcard.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="creditcard.csv not found for evaluation")

    y_full = df["Class"]
    _, test_df = train_test_split(
        df, test_size=0.2, random_state=42, stratify=y_full
    )

    sample = test_df.sample(n=min(sample_size, len(test_df)), random_state=42)

    true_labels = sample["Class"].tolist()
    predictions = []

    for _, row in sample.iterrows():
        scaled_amount = scaler.transform([[row["Amount"]]])[0][0]
        scaled_time = scaler.transform([[row["Time"]]])[0][0]

        features = [row[f"V{i}"] for i in range(1, 29)]
        features.append(scaled_amount)
        features.append(scaled_time)

        pred = model.predict([features])[0]
        predictions.append(int(pred))

    return {
        "sample_size": len(sample),
        "held_out_test_set_size": len(test_df),
        "accuracy": round(accuracy_score(true_labels, predictions), 4),
        "precision": round(precision_score(true_labels, predictions, zero_division=0), 4),
        "recall": round(recall_score(true_labels, predictions, zero_division=0), 4),
        "f1_score": round(f1_score(true_labels, predictions, zero_division=0), 4),
        "baseline_comparison": MODEL_METADATA.get("baseline_metrics", {})
    }

def get_next_version(current_version: str) -> str:
    """Bumps the patch number of a version string. E.g., "1.0.3" -> "1.0.4"""
    parts = current_version.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)





@app.post("/retrain")
def retrain_model():
    """
    Retrains the fraud model from scratch using the creditcard.csv, using the same methodology as the original notebook.
    Saves the result as a NEW version folder and
    switches active_version.txt to point to it -- the old version stays on
    disk untouched, so you can always roll back to it manually if needed.
    """
    global MODEL_VERSION

    try:
        df = pd.read_csv("creditcard.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="creditcard.csv not found for retraining")
    



    new_scaler = RobustScaler()
    df["scaled_amount"] = new_scaler.fit_transform(df["Amount"].values.reshape(-1, 1))
    df["scaled_time"] = new_scaler.fit_transform(df["Time"].values.reshape(-1, 1))

    X = df.drop(["Time","Amount", "Class"], axis=1)
    y = df["Class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
        )
    



    
    neg_count, pos_count = np.bincount(y_train)
    weight_ratio = neg_count / pos_count

    new_model = XGBClassifier(
        scale_pos_weight=weight_ratio,
        use_label_encoder=False,
        random_state=42,
        eval_metric="logloss"
    )
    new_model.fit(X_train, y_train)


    y_pred = new_model.predict(X_test)
    new_metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "fraud_precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "fraud_recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "fraud_f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
    }

    check_performance_and_alert(new_metrics)

    new_version = get_next_version(MODEL_VERSION)
    new_version_dir = os.path.join(MODELS_DIR, new_version)
    os.makedirs(new_version_dir, exist_ok=True)

    joblib.dump(new_model, os.path.join(new_version_dir, "model.pkl"))
    joblib.dump(new_scaler, os.path.join(new_version_dir, "scaler.pkl"))

    new_metadata = {
        "model_name" : "XGBoost Credit Card Fraud Detector",
        "version" : new_version,
        "trained_at": datetime.now().isoformat(),
        "framework": "xgboost",
        "baseline_metrics" : new_metrics
    }

    with open(os.path.join(new_version_dir, "metadata.json"), "w") as f:
        json.dump(new_metadata, f, indent=2)

    with open(os.path.join(MODELS_DIR, "active_version.txt"), "w") as f:
        f.write(new_version)

    load_active_model()

    return {
        "message": f"Retraining complete. New model version {new_version} is now active.",
        "new_version": new_version,
        "metrics": new_metrics
    }





@app.get("/model-info")
def model_info():
    """Reports which model is currently loaded"""
    if MODEL_VERSION is None:
        raise HTTPException(status_code=503, detail="No model loaded")
    
    return{
        "model_version": MODEL_VERSION,
        "metadata": MODEL_METADATA
    }

@app.get("/alerts")
def get_alerts():
    """Returns logged performance alerts from the SQLite database, ordered by most recent first."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, metric_name, value, treshold, message FROM alerts ORDER BY timestamp DESC")
        rows = cursor.fetchall()

    return{
        "alert_count": len(rows),
        "alerts": [
            {
                "timestamp": row[0],
                "metric_name": row[1],
                "value": row[2],
                "treshold": row[3],
                "message": row[4]
            } for row in rows
        ]
    }


def calculate_psi(expected, actual, buckets=10):
    """Calculates the PSI(Population Stability Index)."""

    breakpoints = np.linspace(0, 100, buckets + 1)
    bucket_edges = np.percentile(expected, breakpoints)
    bucket_edges[0] -= 1e-6
    bucket_edges[-1] += 1e-6

    expected_counts = np.histogram(expected, bins=bucket_edges)[0]
    actual_counts = np.histogram(actual, bins=bucket_edges)[0]

    expected_percents = expected_counts / len(expected)
    actual_percents = actual_counts / len(actual)

    expected_percents = np.clip(expected_percents, 1e-6, None)
    actual_percents = np.clip(actual_percents, 1e-6, None)

    psi = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
    return psi


DRIFT_PSI_THRESHOLD = 0.25

@app.get("/drift-check")
def drift_check(recent_n: int = 500):
    """
    Compares the feature distributions of the most recent logged predictions against the original training data,using PSI per feature"""

    with sqlite3.connect(DB_FILE) as conn:
        recent_df = pd.read_sql_query(
            f"SELECT * FROM prediction_logs ORDER BY id DESC LIMIT {recent_n}", conn
            )
        
    if len(recent_df) < 30:
        raise HTTPException(status_code=400, detail="Not enough recent predictions to perform drift check (need at least 30)")
    
    try:
        train_df = pd.read_csv("creditcard.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="creditcard.csv not found for drift check")
    
    db_columns = [f"v{i}" for i in range(1, 29)] + ["amount", "time_feature"]
    csv_columns = [f"V{i}" for i in range(1, 29)] + ["Amount", "Time"]

    drift_results = {}
    for db_col, csv_col in zip(db_columns, csv_columns):
        psi = round(float(calculate_psi(train_df[csv_col], recent_df[db_col].values)), 4)
        drift_results[csv_col] = psi

        if psi > DRIFT_PSI_THRESHOLD:
            log_alert(f"PSI_{csv_col}", psi, DRIFT_PSI_THRESHOLD)

        drifted_features = {k: v for k,v in drift_results.items() if v > DRIFT_PSI_THRESHOLD}

    return {
        "checked_predictions": len(recent_df),
        "psi_by_feature": drift_results,
        "drifted_features": drifted_features,
        "drift_detected": len(drifted_features) > 0
    }

@app.get("/sample-transaction")
def get_sample_transaction(fraud: bool = False):
    """
    Returns a real transaction from creditcard.csv -- useful for quickly
    testing /predict without manually typing 30 values. Pass ?fraud=true
    to get a known fraud example instead of a legitimate one.
    """
    try:
        df = pd.read_csv("creditcard.csv")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="creditcard.csv not found")

    target_class = 1 if fraud else 0
    subset = df[df["Class"] == target_class]

    if len(subset) == 0:
        raise HTTPException(status_code=404, detail="No matching transactions found")

    row = subset.sample(n=1).iloc[0]

    sample = {"Time": float(row["Time"]), "Amount": float(row["Amount"])}
    for i in range(1, 29):
        sample[f"V{i}"] = float(row[f"V{i}"])

    return sample

@app.get("/predictions/recent")
def get_recent_predictions(limit: int = 20):
    """Returns the most recent logged predictions, most recent first --
    used by the frontend for history tables and charts."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, amount, prediction, fraud_probability, model_version
            FROM prediction_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()

    return {
        "predictions": [
            {
                "timestamp": row[0],
                "amount": row[1],
                "is_fraud": row[2],
                "fraud_probability": row[3],
                "model_version": row[4]
            } for row in rows
        ]
    }