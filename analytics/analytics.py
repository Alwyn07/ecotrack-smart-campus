import os
import sys
import pandas as pd

# --------------------------------------------------
# ECOTRACK ANALYTICS ENGINE
# --------------------------------------------------

# Add the Firebase folder to Python's module search path.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIREBASE_DIR = os.path.join(BASE_DIR, "firebase")

sys.path.insert(0, FIREBASE_DIR)

from firebase_config import db


def fetch_readings():
    """Fetch energy readings from Firebase Firestore."""

    print("\nConnecting to Firestore...")

    documents = db.collection("readings").stream()

    records = [document.to_dict() for document in documents]

    if not records:
        raise ValueError(
            "No readings found in Firestore collection 'readings'."
        )

    df = pd.DataFrame(records)

    print(f"Successfully fetched {len(df)} readings.")

    return df


def prepare_data(df):
    """Validate and prepare the energy data."""

    required_columns = [
        "timestamp",
        "building",
        "room",
        "occupancy",
        "voltage",
        "current",
        "power",
        "energy",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    numeric_columns = [
        "occupancy",
        "voltage",
        "current",
        "power",
        "energy",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        )

    df["occupancy"] = df["occupancy"].astype(int)

    return df


def calculate_campus_summary(df):
    """Calculate overall campus power and energy statistics."""

    total_records = len(df)

    # Each room has a separate reading at each simulated time.
    # Summing room power gives total campus power for each time.
    campus_power_by_time = (
        df.groupby("timestamp")["power"].sum()
    )

    average_campus_power = campus_power_by_time.mean()
    peak_campus_power = campus_power_by_time.max()
    peak_time = campus_power_by_time.idxmax()

    # Each room's energy reading represents energy for one
    # simulated hour in the current dataset.
    total_recorded_energy = df["energy"].sum()

    print("\n" + "=" * 60)
    print("ECOTRACK CAMPUS ENERGY SUMMARY")
    print("=" * 60)

    print(f"Total readings: {total_records}")
    print(f"Buildings monitored: {df['building'].nunique()}")
    print(f"Rooms monitored: {df['room'].nunique()}")
    print(f"Simulated timestamps: {df['timestamp'].nunique()}")

    print(
        f"Average campus power: "
        f"{average_campus_power / 1000:.2f} kW"
    )

    print(
        f"Peak campus power: "
        f"{peak_campus_power / 1000:.2f} kW"
    )

    print(f"Peak usage time: {peak_time}")

    print(
        f"Sum of recorded room energy: "
        f"{total_recorded_energy:.2f} kWh"
    )

    return campus_power_by_time


def analyze_buildings(df):
    """Calculate power and energy statistics by building."""

    report = (
        df.groupby("building")
        .agg(
            average_room_power=("power", "mean"),
            peak_room_power=("power", "max"),
            total_recorded_energy=("energy", "sum"),
            readings=("room", "count"),
        )
        .reset_index()
    )

    report = report.sort_values(
        by="total_recorded_energy",
        ascending=False
    )

    print("\n" + "=" * 60)
    print("BUILDING-WISE ANALYSIS")
    print("=" * 60)

    print(report.to_string(index=False))

    return report


def analyze_rooms(df):
    """Calculate power and energy statistics by room."""

    report = (
        df.groupby(["building", "room"])
        .agg(
            average_power=("power", "mean"),
            maximum_power=("power", "max"),
            total_recorded_energy=("energy", "sum"),
            average_occupancy=("occupancy", "mean"),
        )
        .reset_index()
    )

    report = report.sort_values(
        by="total_recorded_energy",
        ascending=False
    )

    print("\n" + "=" * 60)
    print("ROOM-WISE ANALYSIS")
    print("=" * 60)

    print(report.to_string(index=False))

    return report


def analyze_peak_usage(campus_power_by_time):
    """Identify the simulated time with the highest campus load."""

    report = (
        campus_power_by_time
        .rename("campus_power")
        .reset_index()
    )

    report["campus_power_kw"] = (
        report["campus_power"] / 1000
    )

    report = report.sort_values(
        by="campus_power",
        ascending=False
    )

    print("\n" + "=" * 60)
    print("CAMPUS POWER BY SIMULATED TIME")
    print("=" * 60)

    print(report.to_string(index=False))

    return report


def detect_energy_waste(df, power_threshold=500):
    """
    Flag readings where a room is unoccupied but consumes
    more than the specified power threshold.
    """

    alerts = df[
        (df["occupancy"] == 0)
        & (df["power"] > power_threshold)
    ].copy()

    alerts["alert"] = (
        "High power consumption while room is unoccupied"
    )

    print("\n" + "=" * 60)
    print("ENERGY-WASTE ALERTS")
    print("=" * 60)

    if alerts.empty:
        print("No energy-waste conditions detected.")
    else:
        print(f"Alerts detected: {len(alerts)}")

        print(
            alerts[
                [
                    "timestamp",
                    "building",
                    "room",
                    "occupancy",
                    "power",
                    "alert",
                ]
            ].to_string(index=False)
        )

    return alerts


def export_reports(
    campus_power_by_time,
    building_report,
    room_report,
    peak_report,
    alerts,
):
    """Save analytics reports to the project's data folder."""

    output_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(output_dir, exist_ok=True)

    campus_power_by_time.rename(
        "campus_power_w"
    ).reset_index().to_csv(
        os.path.join(output_dir, "campus_power_report.csv"),
        index=False,
    )

    building_report.to_csv(
        os.path.join(output_dir, "building_report.csv"),
        index=False,
    )

    room_report.to_csv(
        os.path.join(output_dir, "room_report.csv"),
        index=False,
    )

    peak_report.to_csv(
        os.path.join(output_dir, "peak_usage_report.csv"),
        index=False,
    )

    alerts.to_csv(
        os.path.join(output_dir, "energy_waste_alerts.csv"),
        index=False,
    )

    print("\n" + "=" * 60)
    print("REPORT EXPORT")
    print("=" * 60)

    print(f"Reports saved to: {output_dir}")

    print("1. campus_power_report.csv")
    print("2. building_report.csv")
    print("3. room_report.csv")
    print("4. peak_usage_report.csv")
    print("5. energy_waste_alerts.csv")


def main():
    df = fetch_readings()
    df = prepare_data(df)

    campus_power_by_time = calculate_campus_summary(df)

    building_report = analyze_buildings(df)
    room_report = analyze_rooms(df)
    peak_report = analyze_peak_usage(campus_power_by_time)

    alerts = detect_energy_waste(df)

    export_reports(
        campus_power_by_time,
        building_report,
        room_report,
        peak_report,
        alerts,
    )

    print("\nEcoTrack analytics completed successfully!")


if __name__ == "__main__":
    main()