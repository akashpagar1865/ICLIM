import os                                                  #file paths, checking if files exist.
import json      

##regular expressions, for cleaning log lines. RegEx finds patterns and replaces it.
# In this case, ReEx is used for removing timestamps and server name prefix in logs.                                           
import re      

from typing import List, Tuple                             #type hints for function return types. 

import pandas as pd                                        #to store classified logs in a DataFrame.
from sklearn.feature_extraction.text import TfidfVectorizer #converts text → numeric features (word importance).
from sklearn.linear_model import LogisticRegression         #the classifier model.
from sklearn.pipeline import Pipeline                       #glues TF-IDF and classifier together into one object.
from sklearn.metrics import classification_report           #prints precision/recall/F1, just as a sanity check.
import joblib                                               #saves/loads the trained model to/from disk.

LOG_FILE = "data/simulated_logs.txt"
MODEL_FILE = "models/log_classifier.pkl"

#Function to clean log line – make logs ML-friendly
def clean_log_line (line : str) -> str:
    """
    Basic log cleaning:
    - Remove leading timestamp + hostname (approx pattern)
    - Lowercase
    - Strip extra spaces
    """

    # Remove leading "Jan 12 10:15:23 server1 " style prefix
    line = re.sub(r"^[A-Z][a-z]{2}\s+\d+\s+\d{2}:\d{2}:\d{2}\s+\S+\s+", "", line)
    line = line.lower()
    line = line.strip()

    return line

#Function to build training data – mini labelled dataset
def build_training_data() -> tuple[list[str], list[str]]:
    """
    Create a small labeled training set using typical log patterns.
    In a real system you would grow this over time or label real logs.
    """
    samples =[

        # SECURITY-ish: failed logins, sudo, auth
        ("sshd[1235]: failed password for invalid user root from 10.0.0.5 port 55221 ssh2", "security"),
        ("sshd[1236]: failed password for invalid user admin from 10.0.0.5 port 55222 ssh2", "security"),
        ("sshd[1237]: failed password for root from 10.0.0.6 port 51432 ssh2", "security"),
        ("sshd[1238]: failed password for root from 10.0.0.6 port 51433 ssh2", "security"),
        ("sudo[3001]: akash : tty=pts/0 ; pwd=/home/akash ; command=/bin/systemctl restart httpd", "security"),

        # ERROR-ish: http 500, backup failure, disk full, high temp
        ("httpd[2224]: 500 internal server error get /api/v1/payments from 203.0.113.6", "error"),
        ("backup[4002]: backup failed: permission denied for /etc/shadow", "error"),
        ("kernel: disk sda1 running out of space: 92% used", "error"),
        ("kernel: cpu temperature above threshold, cpu clock throttled", "error"),

        # WARNING / degraded but not full error
        ("httpd[2223]: 404 not found get /does-not-exist from 203.0.113.5", "warning"),
        ("kernel: disk sda1 usage back to normal: 70% used", "warning"),
        ("kernel: cpu temperature back to normal", "warning"),

        # INFO / normal operations
        ("sshd[1234]: accepted password for user akash from 192.168.1.10 port 54321 ssh2", "info"),
        ("sshd[1239]: accepted password for user dev from 192.168.1.20 port 60123 ssh2", "info"),
        ("systemd[1]: starting daily apt upgrade and clean activities...", "info"),
        ("systemd[1]: finished daily apt upgrade and clean activities.", "info"),
        ("cron[2001]: (root) cmd (/usr/lib64/sa/sa1 1 1)", "info"),
        ("httpd[2222]: 200 ok get /index.html from 203.0.113.5", "info"),
        ("systemd[1]: started backup job daily-backup.service.", "info"),
        ("backup[4001]: backup completed successfully for /var/www", "info"),
    ]

    texts = [clean_log_line(t) for t, _ in samples]
    labels = [label for _, label in samples]

    return texts, labels

#Function to train and save model – build + persist the model
def train_and_save_model() -> Pipeline:                   #Returns the trained Scikit-learn Pipeline object.

    """Train a TF-IDF + LogisticRegression pipeline and save it."""
    X, y = build_training_data()

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000))
        ]
    )

    pipeline.fit(X, y)

    # Quick sanity print
    print("\n=== Training sample classification report (self-eval) ===")
    preds = pipeline.predict(X)
    print(classification_report(y, preds))

    #Saving the model
    os.makedirs(os.path.dirname(MODEL_FILE), exist_ok=True)
    joblib.dump(pipeline, MODEL_FILE)
    print(f"[INFO] Saved log classifier model to {MODEL_FILE}")

    return pipeline

#Function to either load existing model or train a new one
def load_or_train_model() -> Pipeline:
    """Load existing model or train a new one if missing."""
    if os.path.exists(MODEL_FILE):
        print(f"[INFO] Loading existing model from {MODEL_FILE}")
        return joblib.load(MODEL_FILE)
    
    else:
        print("[INFO] No existing model found. Training a new one...")
        return train_and_save_model()
    
#Function to classify_logs – apply model to a log file
def classify_logs(model : Pipeline, log_file : str) -> pd.DataFrame:
    """Classify each log line in the given file."""
    if not os.path.exists(log_file):
        raise FileNotFoundError(f"Log file not found: {log_file}")
    
    rows = []
    with open(log_file, "r") as f:
        for line in f:
            raw = line.strip()
            if not raw:
                continue
            cleaned = clean_log_line(raw)
            label = model.predict([cleaned])[0]
            rows.append({"raw": raw, "cleaned": cleaned, "label": label})

    if not rows:
        print("[WARN] No valid log lines found.")
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    return df      

#Function to summarize_classification – human-friendly summary 
def summarize_classification(df: pd.DataFrame) -> None:
    """Print a small summary of log categories."""
    print("\n=== Log Classification Summary ===")
    counts = df["label"].value_counts()
    for label, count in counts.items():
        print(f"{label.upper():<8}: {count} event(s)")
    print("=================================\n")

    # Example: highlight potential security or error clusters
    security_df = df[df["label"] == "security"]
    error_df = df [df["label"] == "error"]

    if not security_df.empty:
        print("[SECURITY HINT]")
        print(f"- Detected {len(security_df)} security-related event(s).")
        print("  Example:")
        print("  ", security_df.iloc[0]["raw"])

    if not error_df.empty:
        print("\n[ERROR HINT]")
        print(f"- Detected {len(error_df)} error-related event(s).")
        print("  Example:")
        print("  ", error_df.iloc[0]["raw"])
    print()

#Function main – glue it all together
def main():
    model = load_or_train_model()    

    df = classify_logs(model,LOG_FILE)
    if df.empty:
        return
    
    print("\n=== Classified Logs (first 10) ===")
    print(df[["label", "raw"]].head(10).to_string(index=False))

    summarize_classification(df)


if __name__ == "__main__":
    main()







