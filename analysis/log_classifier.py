import os                                                  #file paths, checking if files exist.
import json  
from collections import Counter    

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

LOG_FILE = "data/centos_logs.txt"
MODEL_FILE = "models/log_classifier.pkl"

# quick rule-based patterns for very-high-confidence security lines
SECURITY_PATTERNS = [
    re.compile(r'failed password', re.I),
    re.compile(r'authentication failure', re.I),
    re.compile(r'connection reset by .*preauth', re.I),
    re.compile(r'password check failed', re.I),
    re.compile(r'failed to authenticate', re.I),
    re.compile(r'invalid user', re.I),
]


#Function to clean log line – make logs ML-friendly
def clean_log_line (line : str, remove_numbers: bool = False) -> str:
    """
    Clean a single syslog line to be ML-friendly.

    Steps:
    - Remove leading 'Mon DD HH:MM:SS HOSTNAME ' prefix (flexible)
    - Remove process pid tokens like 'packagekitd[1580]:'
    - Remove IP addresses (optional for some models)
    - Lowercase and collapse whitespace
    - Optionally remove standalone numeric tokens
    """

    if not isinstance(line, str):
        return ""
    
    # 1) Remove leading timestamp + hostname (e.g. "Dec 11 06:27:59 Hostname ")
    # month names (Jan..Dec), day (1-2 digits), time HH:MM:SS, whitespace, hostname (non-greedy)
    line = re.sub(r'^[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\S+\s+', "", line)

    # 2) Remove process name + pid like 'packagekitd[1580]:' or 'sshd[1234]:'
    line = re.sub(r'\b[A-Za-z0-9_\-./]+(?:\[[0-9]+\])?:\s*', '', line)

    # 3) Remove IP addresses
    line = re.sub(r'\b\d{1,3}(?:\.\d{1,3}){3}\b', ' ', line)

    # 4) Optionally remove numbers (timestamps inside message, ports, PIDs etc.)
    if remove_numbers:
        line = re.sub(r'\b\d+\b', ' ', line)

    # 5) Lowercase & collapse whitespace
    line = line.lower()
    line = re.sub(r'\s+', ' ', line).strip()

    return line

#Function to build training data – mini labelled dataset
def build_training_data() -> tuple[list[str], list[str]]:
    """
    Create a small labeled training set using typical log patterns.
    In a real system you would grow this over time or label real logs.
    """
    samples = [

    # ============================
    # SECURITY (auth failures, sudo, suspicious events)
    # ============================
    ("sshd[1235]: failed password for invalid user root from 10.0.0.5 port 55221 ssh2", "security"),
    ("sshd[1236]: failed password for invalid user admin from 10.0.0.5 port 55222 ssh2", "security"),
    ("sshd[1237]: failed password for root from 10.0.0.6 port 51432 ssh2", "security"),
    ("sshd[1238]: failed password for root from 10.0.0.6 port 51433 ssh2", "security"),
    ("unix_chkpwd[2720]: password check failed for user akashp", "security"),
    ("polkitd[745]: Authentication required but no agent is available", "security"),
    ("sudo[3001]: akash : tty=pts/0 ; pwd=/home/akash ; command=/bin/systemctl restart httpd", "security"),

    # Real CentOS security logs
    ("pam_unix(sshd:auth): authentication failure; user=akashp rhost=192.168.1.4", "security"),
    ("sshd-session[2718]: Failed password for akashp from 192.168.1.4 port 64215 ssh2", "security"),
    ("sshd-session[2691]: Connection reset by 192.168.1.4 port 64187 [preauth]", "security"),


    # ============================
    # ERROR (system failures, repo errors, kernel issues)
    # ============================
    ("httpd[2224]: 500 internal server error get /api/v1/payments", "error"),
    ("backup[4002]: backup failed: permission denied for /etc/shadow", "error"),
    ("kernel: disk sda1 running out of space: 92% used", "error"),
    ("kernel: cpu temperature above threshold, cpu clock throttled", "error"),

    # Real CentOS error logs
    ("dnf[2835]: Error: Failed to download metadata for repo 'epel': Yum repo downloading error", "error"),
    ("dnf[2835]: Curl error (28): Timeout was reached while downloading repo metadata", "error"),
    ("systemd[1]: dnf-makecache.service: Main process exited, status=1/FAILURE", "error"),


    # ============================
    # WARNING (degraded, retries, assertion errors)
    # ============================
    ("httpd[2223]: 404 not found get /does-not-exist", "warning"),
    ("kernel: disk sda1 usage back to normal: 70% used", "warning"),
    ("kernel: cpu temperature back to normal", "warning"),

    # Real CentOS warning logs
    ("gnome-shell[1975]: g_object_ref: assertion 'G_IS_OBJECT (object)' failed", "warning"),
    ("kernel: clocksource watchdog on CPU0: kvm-clock retried 1 times before success", "warning"),
    ("rsyslogd[1009]: imjournal: journal files changed, reloading", "warning"),
    ("packagekitd[1580]: Failed to get cache filename for glibc-langpack-en", "warning"),


    # ============================
    # INFO (routine system operations)
    # ============================
    ("systemd[1]: starting daily apt upgrade and clean activities", "info"),
    ("systemd[1]: finished daily apt upgrade and clean activities", "info"),
    ("cron[2001]: (root) cmd (/usr/lib64/sa/sa1 1 1)", "info"),
    ("httpd[2222]: 200 ok get /index.html", "info"),
    ("systemd[1]: started backup job daily-backup.service", "info"),
    ("backup[4001]: backup completed successfully for /var/www", "info"),

    # Real CentOS info logs
    ("systemd[1]: systemd-localed.service: Deactivated successfully", "info"),
    ("systemd[1887]: Started Virtual filesystem metadata service", "info"),
    ("systemd[1]: Starting dnf makecache", "info"),
    ("dnf[2835]: CentOS Stream 9 - BaseOS metadata download successful", "info"),
    ("systemd[1]: packagekit.service: Deactivated successfully", "info"),
    
    ]

    # ----- extra real CentOS samples (cleaned form) -----
    # these are the cleaned strings (same style the clean_log_line produces)
    # Use as many variations as you can collect — keep the labels balanced.

    extra_samples = [
    
    # SECURITY (auth failures, preauth, failed password, auth failure)
    ("failed password for akashp from port 64215 ssh2", "security"),
    ("connection reset by remote host preauth", "security"),
    ("pam_unix(sshd:auth): authentication failure user rhost", "security"),
    ("password check failed for user akashp", "security"),

    # ERROR (dnf/repo failures, dnf-makecache exit failure)
    ("error failed to download metadata for repo epel yum repo downloading error", "error"),
    ("curl error 28 timeout was reached while downloading repo metadata", "error"),
    ("dnf-makecache.service main process exited status failure", "error"),

    # WARNING (assertions, retries, reloads)
    ("g_object_ref assertion g_is_object object failed", "warning"),
    ("clocksource timekeeping watchdog on cpu0 kvm-clock retried 1 times before success", "warning"),
    ("imjournal journal files changed reloading", "warning"),
    ("failed to get cache filename for package glibc-langpack-en", "warning"),

    # INFO (service starts/stops, cron, normal operations)
    ("server listening on 0.0.0.0 port 22", "info"),
    ("systemd localed service deactivated successfully", "info"),
    ("starting dnf makecache", "info"),
    ("crond root cmd run-parts /etc/cron.hourly", "info"),
    ("sudo root tail iclim_centos_logs txt created", "info"),
    ]

    #Extend the main samples list
    samples += extra_samples


    texts = [clean_log_line(t) for t, _ in samples]
    labels = [label for _, label in samples]

    return texts, labels

#Function to train and save model – build + persist the model
def train_and_save_model() -> Pipeline:                   #Returns the trained Scikit-learn Pipeline object.

    """Train a TF-IDF + LogisticRegression pipeline and save it."""
    X, y = build_training_data()

    from collections import Counter
    print("TRAIN LABEL COUNTS:", Counter(y))


    pipeline = Pipeline([
    # ngram_range (1,2) keeps unigrams + bigrams. min_df reduces singletons.
    ("tfidf", TfidfVectorizer(ngram_range=(1,2), min_df=2, max_df=0.9)),
    # class_weight balanced helps when classes are imbalanced
    ("clf", LogisticRegression(max_iter=2000, class_weight="balanced"))
    ])


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
def load_or_train_model(force_retrain: bool = False) -> Pipeline:
    """Load existing model or train a new one if missing (optionally force retrain)."""
    if os.path.exists(MODEL_FILE) and not force_retrain:
        print(f"[INFO] Loading existing model from {MODEL_FILE}")
        return joblib.load(MODEL_FILE)
    else:
        print("[INFO] Training a new model (force_retrain=%s)..." % force_retrain)
        return train_and_save_model()

    
#Function to classify_logs – apply model to a log file
def classify_logs(model : Pipeline, log_file : str) -> pd.DataFrame:
    """Classify each log line in the given file."""
    if not os.path.exists(log_file):
        raise FileNotFoundError(f"Log file not found: {log_file}")
    
    rows = []
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            raw = line.rstrip("\n")
            if not raw:
                continue

            cleaned = clean_log_line(raw)

            # Rule-based override (quick wins). If any pattern matches the raw text,
            # classify as 'security' immediately.
            matched = False
            for p in SECURITY_PATTERNS:
                if p.search(raw):
                    rows.append({"raw": raw, "cleaned": cleaned, "label": "security"})
                    matched = True
                    break
            if matched:
                continue

            # Fallback to ML classifier
            try:
                label = model.predict([cleaned])[0]
            except Exception as e:
                # If model fails for any reason, mark as 'info' (safe default)
                label = "info"
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

    # CI-safe: only classify logs if file exists
    if not os.path.exists(LOG_FILE):
        print(f"[CI INFO] {LOG_FILE} not found — skipping log classification")
        return

    df = classify_logs(model, LOG_FILE)

    if df.empty:
        return

    print("\n=== Classified Logs (first 10) ===")
    print(df[["label", "cleaned", "raw"]].head(10).to_string(index=False))

    summarize_classification(df)


if __name__ == "__main__":
    main()







