import json

# Create dictionary for inputting data to JSON file
data = {
    "cpu" : 20,
    "mem" : 100,
    "disk" : 200,
    "server" : "Linux VM"
}

# Write to JSON file
with open("snapshot_json", "w") as f:
    json.dump(data, f, indent=2)

# Read JSON file
with open("snapshot_json", "r") as f:
    loaded = json.load(f)

# Print JSON file snapshot
print("Loaded snapshot:")
print(loaded)