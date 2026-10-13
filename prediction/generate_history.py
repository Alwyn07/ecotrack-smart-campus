import os
import numpy as np
import pandas as pd

# --------------------------------------------------
# ECOTRACK MULTI-DAY DATA GENERATOR
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

OUTPUT_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(
    OUTPUT_DIR,
    "historical_energy_data.csv"
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

VOLTAGE = 230
DAYS = 30

ROOMS = [
    {
        "building": "Building A",
        "room": "Classroom 101",
        "capacity": 40,
        "led_power": 108,
        "fan_power": 280,
        "ac_power": 1500,
        "projector_power": 300,
        "computers_power": 0,
        "kind": "classroom",
    },
    {
        "building": "Building A",
        "room": "Classroom 102",
        "capacity": 40,
        "led_power": 108,
        "fan_power": 280,
        "ac_power": 1500,
        "projector_power": 0,
        "computers_power": 0,
        "kind": "classroom",
    },
    {
        "building": "Building A",
        "room": "Computer Lab",
        "capacity": 50,
        "led_power": 144,
        "fan_power": 420,
        "ac_power": 0,
        "projector_power": 0,
        "computers_power": 5000,
        "kind": "lab",
    },
    {
        "building": "Building B",
        "room": "Classroom 201",
        "capacity": 40,
        "led_power": 108,
        "fan_power": 280,
        "ac_power": 0,
        "projector_power": 0,
        "computers_power": 0,
        "kind": "classroom",
    },
    {
        "building": "Building B",
        "room": "Laboratory",
        "capacity": 40,
        "led_power": 144,
        "fan_power": 280,
        "ac_power": 3000,
        "projector_power": 0,
        "computers_power": 0,
        "kind": "lab",
    },
    {
        "building": "Building B",
        "room": "Office",
        "capacity": 15,
        "led_power": 72,
        "fan_power": 0,
        "ac_power": 1500,
        "projector_power": 0,
        "computers_power": 750,
        "kind": "office",
    },
]

HOURS = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]

rng = np.random.default_rng(42)
records = []

for day in range(1, DAYS + 1):

    # Simulated weekday/weekend effect.
    # Day 6 and Day 7 of each week have lower occupancy.
    weekday = ((day - 1) % 7) + 1
    is_weekend = weekday >= 6

    for hour in HOURS:

        for room in ROOMS:

            # Determine occupancy.
            if is_weekend or hour < 8 or hour >= 17:
                occupancy = 0
            else:
                maximum = room["capacity"]

                if room["kind"] == "classroom":
                    occupancy = int(
                        rng.integers(
                            max(1, maximum // 3),
                            maximum + 1
                        )
                    )
                elif room["kind"] == "lab":
                    occupancy = int(
                        rng.integers(
                            max(1, maximum // 4),
                            maximum + 1
                        )
                    )
                else:
                    occupancy = int(
                        rng.integers(
                            max(1, maximum // 3),
                            maximum + 1
                        )
                    )

            # Determine appliance states.
            # Lights and fans are generally active when occupied.
            # AC is used during occupied daytime hours.
            # Computers are used in the lab when occupied.
            lights_on = occupancy > 0
            fans_on = occupancy > 0

            ac_on = (
                occupancy > 0
                and 10 <= hour <= 16
                and room["ac_power"] > 0
            )

            projector_on = (
                occupancy > 0
                and hour in [9, 10, 14]
                and room["projector_power"] > 0
            )

            computers_on = (
                occupancy > 0
                and room["computers_power"] > 0
            )

            # Introduce occasional simulated wastage.
            # This represents equipment accidentally left on.
            if occupancy == 0 and rng.random() < 0.08:
                lights_on = True

            if occupancy == 0 and rng.random() < 0.04:
                ac_on = room["ac_power"] > 0

            power = 0

            if lights_on:
                power += room["led_power"]

            if fans_on:
                power += room["fan_power"]

            if ac_on:
                power += room["ac_power"]

            if projector_on:
                power += room["projector_power"]

            if computers_on:
                power += room["computers_power"]

            # Energy represents one simulated hour.
            energy = power / 1000

            current = power / VOLTAGE

            records.append(
                {
                    "day": day,
                    "weekday": weekday,
                    "is_weekend": int(is_weekend),
                    "timestamp": f"{hour:02d}:00",
                    "hour": hour,
                    "building": room["building"],
                    "room": room["room"],
                    "occupancy": occupancy,
                    "voltage": VOLTAGE,
                    "current": round(current, 2),
                    "power": power,
                    "energy": round(energy, 3),
                }
            )

df = pd.DataFrame(records)

df.to_csv(OUTPUT_FILE, index=False)

print("=" * 60)
print("ECOTRACK HISTORICAL DATA GENERATOR")
print("=" * 60)

print(f"Simulated days: {DAYS}")
print(f"Rooms: {len(ROOMS)}")
print(f"Hours per day: {len(HOURS)}")
print(f"Total records: {len(df)}")
print(f"Saved to: {OUTPUT_FILE}")

print("\nPreview:")
print(df.head(10).to_string(index=False))