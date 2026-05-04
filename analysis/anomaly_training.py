import pandas as pd
from sklearn.ensemble import IsolationForest
import json
import joblib

#Function to load & prepare history data
def load_history(filename):
    records = []
    with open(filename, "r") as f:
        for line in f:
            records.append(json.loads(line.strip()))
    return pd.DataFrame(records)

def prepare_df(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df= df.sort_values("timestamp")
    return df

#Function to extract features for ML
def get_features(df):
    return df[["cpu", "mem", "disk"]]

#Function to Train IsolationForest
def train_model(features):
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05, #Approx % anomalies expected
        random_state=42
    )
    model.fit(features)
    return model

#Function to Predict anomalies
def detect_anomalies(model, features, df):
    preds = model.predict(features)
    # IsolationForest: 1 = normal, -1 = anomaly
    df["anomaly"] = preds
    return df

#Function to save model
def save_model(model):
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    MODEL_PATH = os.path.join(BASE_DIR, "models", "anomaly_model.pkl")

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)

    joblib.dump(model, MODEL_PATH)
    print("Model saved at:", MODEL_PATH)

#Main logic

import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
history_file = os.path.join(BASE_DIR, "logs", "snapshot_history.jsonl")

df = load_history(history_file)
df = prepare_df(df)

features = get_features(df)
model = train_model(features)

df = detect_anomalies(model, features, df)

print("\n--- Anomaly Detection Results ---")
print(df[["timestamp", "cpu", "mem", "disk", "anomaly"]])

save_model(model)
