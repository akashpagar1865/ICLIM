import pandas as pd
from sklearn.ensemble import IsolationForest
import json
import joblib
import os
from utils.logger import setup_logger

logger = setup_logger()

CONTAMINATION = 0.05
MIN_TRAINING_SAMPLES = 20
ANOMALY_RATE_TOLERANCE = 0.01


def load_history(filename):
    records = []

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            records.append(json.loads(line))

    return pd.DataFrame(records)


def prepare_df(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    return df


def get_features(df):
    required_columns = ["cpu", "mem", "disk"]

    missing = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required training features: {missing}"
        )

    return df[required_columns]


def train_model(features):
    model = IsolationForest(
        n_estimators=200,
        contamination=CONTAMINATION,
        random_state=42
    )

    model.fit(features)

    return model


def validate_model(model, features):
    predictions = model.predict(features)

    if len(predictions) != len(features):
        raise ValueError(
            "Model prediction count does not match training data."
        )

    anomaly_count = (predictions == -1).sum()
    anomaly_rate = anomaly_count / len(predictions)

    lower_bound = CONTAMINATION - ANOMALY_RATE_TOLERANCE
    upper_bound = CONTAMINATION + ANOMALY_RATE_TOLERANCE

    logger.info(
        f"Candidate model anomaly rate: "
        f"{anomaly_rate * 100:.2f}%"
    )

    if not lower_bound <= anomaly_rate <= upper_bound:
        raise ValueError(
            f"Candidate model anomaly rate "
            f"{anomaly_rate * 100:.2f}% is outside the "
            f"expected range "
            f"{lower_bound * 100:.2f}% - "
            f"{upper_bound * 100:.2f}%."
        )

    logger.info("Candidate model validation passed.")

    return True


def save_model(model, model_path):

    os.makedirs(
        os.path.dirname(model_path),
        exist_ok=True
    )

    candidate_path = model_path + ".candidate"

    joblib.dump(
        model,
        candidate_path
    )

    logger.info(
        f"Candidate model saved at: {candidate_path}"
    )

    return candidate_path


def activate_model(candidate_path, model_path):

    os.replace(
        candidate_path,
        model_path
    )

    logger.info(
        f"Candidate model activated: {model_path}"
    )


def train_from_history(history_file, model_path):

    logger.info(
        f"Starting model training from: {history_file}"
    )

    df = load_history(history_file)

    if df.empty:
        raise ValueError(
            "History contains no training data."
        )

    df = prepare_df(df)

    if len(df) < MIN_TRAINING_SAMPLES:
        raise ValueError(
            f"Not enough training samples. "
            f"Found {len(df)}, "
            f"minimum required is {MIN_TRAINING_SAMPLES}."
        )

    features = get_features(df)

    logger.info(
        f"Training model using {len(features)} snapshots."
    )

    model = train_model(features)

    validate_model(
        model,
        features
    )

    candidate_path = save_model(
        model,
        model_path
    )

    activate_model(
        candidate_path,
        model_path
    )

    logger.info(
        "Model training and activation completed successfully."
    )

    return model


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

    train_from_history(
        history_file,
        model_path
    )
