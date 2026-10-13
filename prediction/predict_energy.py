import os
import joblib
import pandas as pd

# --------------------------------------------------
# ECOTRACK NEXT-DAY ENERGY FORECAST
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "models",
    "energy_prediction_model.joblib",
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "historical_energy_data.csv",
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "next_day_forecast.csv",
)

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(
        "Trained model not found. Run train_model.py first."
    )

if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(
        "Historical data not found. Run generate_history.py first."
    )

model = joblib.load(MODEL_FILE)

history = pd.read_csv(DATA_FILE)

last_day = int(history["day"].max())
next_day = last_day + 1

next_weekday = ((next_day - 1) % 7) + 1
is_weekend = int(next_weekday >= 6)

hours = sorted(history["hour"].unique())

rooms = history[
    ["building", "room"]
].drop_duplicates()

average_occupancy = (
    history.groupby(
        ["building", "room", "hour"]
    )["occupancy"]
    .mean()
)

records = []

for _, room in rooms.iterrows():

    for hour in hours:

        key = (
            room["building"],
            room["room"],
            hour,
        )

        occupancy = float(
            average_occupancy.get(key, 0)
        )

        # MVP assumption: no occupants on weekends.
        if is_weekend:
            occupancy = 0

        input_row = pd.DataFrame(
            [
                {
                    "weekday": next_weekday,
                    "is_weekend": is_weekend,
                    "hour": int(hour),
                    "building": room["building"],
                    "room": room["room"],
                    "occupancy": occupancy,
                }
            ]
        )

        predicted_power = max(
            0.0,
            float(model.predict(input_row)[0]),
        )

        records.append(
            {
                "day": next_day,
                "weekday": next_weekday,
                "timestamp": f"{int(hour):02d}:00",
                "building": room["building"],
                "room": room["room"],
                "predicted_occupancy": round(
                    occupancy,
                    1,
                ),
                "predicted_power_w": round(
                    predicted_power,
                    2,
                ),
                "predicted_energy_kwh": round(
                    predicted_power / 1000,
                    3,
                ),
            }
        )

forecast = pd.DataFrame(records)

forecast.to_csv(
    OUTPUT_FILE,
    index=False,
)

campus_forecast = (
    forecast.groupby("timestamp")
    .agg(
        predicted_campus_power_w=(
            "predicted_power_w",
            "sum",
        ),
        predicted_campus_energy_kwh=(
            "predicted_energy_kwh",
            "sum",
        ),
    )
    .reset_index()
)

print("=" * 60)
print("ECOTRACK NEXT-DAY ENERGY FORECAST")
print("=" * 60)

print(f"Forecast day index: {next_day}")
print(f"Rooms forecast: {forecast['room'].nunique()}")
print(f"Hours forecast: {forecast['timestamp'].nunique()}")

print("\nCampus forecast by time:")
print(campus_forecast.to_string(index=False))

# Calculate the total from unrounded power values.
total_energy = (
    forecast["predicted_power_w"].sum()
    / 1000
)

peak_index = campus_forecast[
    "predicted_campus_power_w"
].idxmax()

peak_row = campus_forecast.loc[peak_index]

print(
    "\nTotal predicted energy for the simulated day: "
    f"{total_energy:.2f} kWh"
)

print(
    "Peak predicted demand: "
    f"{peak_row['predicted_campus_power_w'] / 1000:.2f} kW "
    f"at {peak_row['timestamp']}"
)

print(f"\nDetailed forecast saved to: {OUTPUT_FILE}")