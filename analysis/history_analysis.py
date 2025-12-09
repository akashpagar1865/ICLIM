import pandas as pd
import json

#Function to load JSONL file into Pandas
def load_history(filename):
    records = []
    with open(filename, "r") as f:
        for line in f:
            records.append(json.loads(line.strip()))

    return pd.DataFrame(records)

#Function to convert timestamp into datetime
def prepare_dataframe(df):
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    return df

#Function to show first few rows
def preview(df):
    print("\n --- Preview of Data ---")
    print(df.head())

#Function to show summary statistics
def summary(df):
    print("\n--- Sumaary Statisctics ---")
    print(df[["cpu", "mem", "disk"]].describe())

#Function to detect CPU Spikes Manually
def detect_spikes(df, threshold=5):
    spikes = df[df["cpu"] > threshold]
    print(f"\n CPU spikes > {threshold}%:")
    print(spikes[["timestamp", "cpu"]])

#Function to show latest snapshot
def latest(df):
           print("\n Latest Snapshot:")
           print(df.tail(1))

history_file = "snapshot_history.jsonl"

df = load_history(history_file)
df = prepare_dataframe(df)

preview(df)
summary(df)
detect_spikes(df, threshold=5)
latest(df)
