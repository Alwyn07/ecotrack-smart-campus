import pandas as pd
from firebase_config import db
import os

# Path to CSV file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "sample_data.csv")

# Load CSV
df = pd.read_csv(CSV_PATH)

print("=" * 60)
print("ECOTRACK FIREBASE UPLOAD")
print("=" * 60)

print(f"\nRecords found: {len(df)}")

# Firestore collection
collection = db.collection("readings")

# Upload each record
for index, row in df.iterrows():

    data = {
        "timestamp": str(row["timestamp"]),
        "building": str(row["building"]),
        "room": str(row["room"]),
        "occupancy": int(row["occupancy"]),
        "voltage": float(row["voltage"]),
        "current": float(row["current"]),
        "power": float(row["power"]),
        "energy": float(row["energy"])
    }

    collection.add(data)

    print(
        f"Uploaded {index + 1}/{len(df)}: "
        f"{row['timestamp']} - "
        f"{row['building']} - "
        f"{row['room']}"
    )

print("\n" + "=" * 60)
print("UPLOAD COMPLETED")
print("=" * 60)

print(f"\nTotal records uploaded: {len(df)}")
print("Firestore collection: readings")