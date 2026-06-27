import pandas as pd
from sklearn.ensemble import IsolationForest
import json
import joblib
import os
from utils.logger import setup_logger

logger = setup_logger()


# Historical JSONL data is converted into a
# pandas dataframe so it can be processed by
# scikit-learn.

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

# Only numeric metrics are used for training.
# Timestamp is useful for ordering but is not
# included as a model feature.

#Function to extract features for ML
def get_features(df):
    return df[["cpu", "mem", "disk"]]

# Isolation Forest learns normal system behavior
# using CPU, Memory and Disk usage.
# Later, realtime metrics are compared against
# this baseline to identify unusual patterns.

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
def save_model(model, model_path):

    os.makedirs(os.path.dirname(model_path), exist_ok=True)

    joblib.dump(model, model_path)

    logger.info(f"Model saved at: {model_path}")

#Function to train from history
def train_from_history(history_file, model_path):

    # Complete training pipeline:
    # Load history -> Prepare data -> Train model -> Save model
    
    df = load_history(history_file)
    df = prepare_df(df)

    features = get_features(df)

    model = train_model(features)

    df = detect_anomalies(
        model,
        features,
        df
    )

    save_model(model, model_path)

    return model

#Main logic
if __name__ == "__main__":

    BASE_DIR = os.path.dirname(
        os.path.dirname(__file__)
    )

    history_file = os.path.join(
    BASE_DIR,
    "logs",
    "snapshot_history.jsonl"
    )

    model_path = os.path.join(
        BASE_DIR,
        "models",
        "anomaly_model.pkl"
    )

    model = train_from_history(
        history_file,
        model_path
    )

    logger.info("Model Training Complete.")
