import json
import os
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

HISTORY_FILE = "snapshot_history.jsonl"
MODEL_FILE = "anomaly_model.pkl"
KNOWN_ANOMALIES_FILE = "known_anomalies.jsonl"

# How many most recent snapshots to use for training (None = use all)
RECENT_LIMIT = 500

# Whether to skip known anomalies from training if the file exists
SKIP_KNOWN_ANOMALIES = True


def load_history(filename):
    records = []
    bad_lines = 0

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                bad_lines += 1
                # just skip this line and continue

    if bad_lines > 0:
        print(f"Warning: skipped {bad_lines} invalid JSON line(s) in {filename}")

    if not records:
        print("No valid records found in history file.")
        return pd.DataFrame()

    return pd.DataFrame(records)


def prepare_df(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    
    #If timestamps missing, raising error
    if "timestamp" not in df.columns:
      raise KeyError("Expected 'timestamp' column in history data.")

    # Drop exact duplicates
    df = df.drop_duplicates(subset=["timestamp", "cpu", "mem", "disk"])

    # Keep only the most recent N snapshots if RECENT_LIMIT is set
    if RECENT_LIMIT is not None and len(df) > RECENT_LIMIT:
        df = df.tail(RECENT_LIMIT)
        print(f"Using only the most recent {RECENT_LIMIT} snapshots for training.")

    return df


def load_known_anomalies(filename):
    """Return a set of timestamps that should be skipped from training."""
    if not os.path.exists(filename):
        return set()

    timestamps = set()
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if "timestamp" in record:
                    timestamps.add(record["timestamp"])
            except json.JSONDecodeError:
                continue

    return timestamps


def filter_known_anomalies(df):
    if not SKIP_KNOWN_ANOMALIES:
        return df

    known_ts = load_known_anomalies(KNOWN_ANOMALIES_FILE)
    if not known_ts:
        return df

    before = len(df)
    df = df[~df["timestamp"].astype(str).isin(known_ts)]
    after = len(df)

    print(f"Skipped {before - after} snapshot(s) marked as known anomalies.")
    return df


def get_features(df):
    return df[["cpu", "mem", "disk"]]


def train_model(features, contamination=0.05):
    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42
    )
    model.fit(features)
    return model


def main():
    print(f"Loading history from {HISTORY_FILE} ...")
    df = load_history(HISTORY_FILE)

    if df.empty:
        print("No data available to train on. Exiting.")
        return

    df = prepare_df(df)
    df = filter_known_anomalies(df)

    print(f"Total snapshots used for training: {len(df)}")

    # safety check
    if len(df) < 20:
        print("Not enough snapshots to retrain reliably (need at least 20).")
        return

    features = get_features(df)

    print("Training IsolationForest on historical data...")
    model = train_model(features, contamination=0.05)

    # quick sanity check: see how many anomalies it thinks exist in training data
    preds = model.predict(features)
    df["anomaly"] = preds
    num_anom = (df["anomaly"] == -1).sum()
    print(f"Anomalies detected in training data: {num_anom} / {len(df)}")

    joblib.dump(model, MODEL_FILE)
    print(f"✅ Updated model saved to {MODEL_FILE}")


if __name__ == "__main__":
    main()
