#Read snapshot history (JSONL → DataFrame)
import json
import pandas as pd

#Function to create clean dataframe with timestamps sorted
def load_snapshot(path = "data/snapshot_history.jsonl"):

    rows = []

    with open(path, "r") as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            
            except:
                pass

    
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")
    return df