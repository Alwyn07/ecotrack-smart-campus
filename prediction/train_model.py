import os
import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

# --------------------------------------------------
# ECOTRACK ENERGY PREDICTION MODEL
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_FILE = os.path.join(
    BASE_DIR,
    "data",
    "historical_energy_data.csv",
)

MODEL_DIR = os.path.join(BASE_DIR, "models")

MODEL_FILE = os.path.join(
    MODEL_DIR,
    "energy_prediction_model.joblib",
)

EVALUATION_FILE = os.path.join(
    BASE_DIR,
    "data",
    "prediction_evaluation.csv",
)

os.makedirs(MODEL_DIR, exist_ok=True)

df = pd.read_csv(DATA_FILE)

required_columns = [
    "day",
    "weekday",
    "is_weekend",
    "hour",
    "building",
    "room",
    "occupancy",
    "power",
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

df = df.sort_values(
    ["day", "hour", "building", "room"]
).reset_index(drop=True)

print("=" * 60)
print("ECOTRACK MODEL TRAINING")
print("=" * 60)

print(f"Total records: {len(df)}")

# Exclude the numerical day index.
# The model will learn from time, location, and occupancy.
features = [
    "weekday",
    "is_weekend",
    "hour",
    "building",
    "room",
    "occupancy",
]

target = "power"

X = df[features]
y = df[target]

# Chronological split:
# Days 1-24 for training; Days 25-30 for testing.
split_day = 25

train_mask = df["day"] < split_day
test_mask = df["day"] >= split_day

X_train = X.loc[train_mask]
X_test = X.loc[test_mask]

y_train = y.loc[train_mask]
y_test = y.loc[test_mask]

numeric_features = [
    "weekday",
    "is_weekend",
    "hour",
    "occupancy",
]

categorical_features = [
    "building",
    "room",
]

numeric_transformer = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
        (
            "scaler",
            StandardScaler(),
        ),
    ]
)

categorical_transformer = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "onehot",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_transformer,
            numeric_features,
        ),
        (
            "categorical",
            categorical_transformer,
            categorical_features,
        ),
    ]
)

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "regressor",
            RandomForestRegressor(
                n_estimators=300,
                random_state=42,
                min_samples_leaf=1,
                n_jobs=-1,
            ),
        ),
    ]
)

model.fit(X_train, y_train)

predictions = model.predict(X_test)

# General evaluation metrics.
mae = mean_absolute_error(y_test, predictions)

rmse = mean_squared_error(
    y_test,
    predictions,
) ** 0.5

r2 = r2_score(y_test, predictions)

print("\nMODEL EVALUATION")
print("-" * 60)

print(f"Training records: {len(X_train)}")
print(f"Testing records: {len(X_test)}")
print(f"MAE: {mae:.2f} W")
print(f"RMSE: {rmse:.2f} W")
print(f"R²: {r2:.3f}")

# Build an evaluation report.
evaluation = df.loc[
    test_mask,
    [
        "day",
        "weekday",
        "timestamp",
        "hour",
        "building",
        "room",
        "occupancy",
        "power",
    ],
].copy()

evaluation["predicted_power"] = predictions.round(2)

evaluation["error_w"] = (
    evaluation["predicted_power"]
    - evaluation["power"]
)

evaluation["absolute_error_w"] = (
    evaluation["error_w"].abs()
)

# Evaluate zero-occupancy records separately.
unoccupied = evaluation[
    evaluation["occupancy"] == 0
]

print("\nUNOCCUPIED ROOM EVALUATION")
print("-" * 60)

if not unoccupied.empty:
    unoccupied_mae = mean_absolute_error(
        unoccupied["power"],
        unoccupied["predicted_power"],
    )

    print(f"Unoccupied records: {len(unoccupied)}")
    print(f"Unoccupied MAE: {unoccupied_mae:.2f} W")

    # High-power events are defined here as actual power > 500 W.
    high_power_events = unoccupied[
        unoccupied["power"] > 500
    ]

    print(
        "Unoccupied readings above 500 W: "
        f"{len(high_power_events)}"
    )

    if not high_power_events.empty:
        print("\nHigh-power event predictions:")
        print(
            high_power_events[
                [
                    "day",
                    "timestamp",
                    "building",
                    "room",
                    "power",
                    "predicted_power",
                    "absolute_error_w",
                ]
            ].to_string(index=False)
        )
else:
    print("No unoccupied records in the test dataset.")

# Room-wise evaluation.
print("\nROOM-WISE EVALUATION")
print("-" * 60)

room_metrics = (
    evaluation.groupby(["building", "room"])
    .agg(
        MAE_W=("absolute_error_w", "mean"),
        Max_Error_W=("absolute_error_w", "max"),
        Records=("power", "count"),
    )
    .round(2)
)

print(room_metrics.to_string())

# Save evaluation output.
evaluation.to_csv(
    EVALUATION_FILE,
    index=False,
)

# Save the complete model pipeline.
joblib.dump(model, MODEL_FILE)

print(f"\nModel saved to: {MODEL_FILE}")
print(f"Evaluation saved to: {EVALUATION_FILE}")
print("\nTraining completed.")