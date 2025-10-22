import os
import json

import pandas as pd
from sklearn.model_selection import train_test_split
import xgboost as xgb

from utils import data_dir, feature_cols


def train_models():
    combined_file_path = os.path.join(data_dir, 'combined.csv')
    if not os.path.exists(combined_file_path):
        print("Combined dataset not found; run preprocessing first.")
        return

    metadata_file = os.path.join(data_dir, 'training_metadata.json')
    combined_mtime = os.path.getmtime(combined_file_path)
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        except (OSError, json.JSONDecodeError):
            metadata = {}
        if metadata.get('combined_mtime') == combined_mtime:
            print("Modelle aktuell, Training übersprungen")
            return

    df = pd.read_csv(combined_file_path)
    # Ensure numeric columns are of proper dtype
    for col in ["Prediction", "Consent", "Maybe"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    cat_type = pd.api.types.CategoricalDtype(
        categories=df["Category"].unique(), ordered=True
    )

    df = df.sort_values(by=["Event_ID", "Delta"])
    df["Prediction_lag1"] = df.groupby("Event_ID")["Prediction"].shift(1)
    df["Consent_lag1"] = df.groupby("Event_ID")["Consent"].shift(1)
    df["Maybe_lag1"] = df.groupby("Event_ID")["Maybe"].shift(1)
    df["Category_enc"] = df["Category"].astype(cat_type).cat.codes

    X = df[feature_cols]
    y_pred = df["Prediction"]
    y_consent = df["Consent"]
    y_maybe = df["Maybe"]

    X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(
        X, y_pred, test_size=0.2, random_state=42
    )
    X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
        X, y_consent, test_size=0.2, random_state=42
    )
    X_train_m, X_test_m, y_train_m, y_test_m = train_test_split(
        X, y_maybe, test_size=0.2, random_state=42
    )

    model_pred = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
    model_pred.fit(X_train_p, y_train_p)
    model_consent = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
    model_consent.fit(X_train_c, y_train_c)
    model_maybe = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
    model_maybe.fit(X_train_m, y_train_m)

    model_pred.save_model(os.path.join(data_dir, 'model_prediction.json'))
    model_consent.save_model(os.path.join(data_dir, 'model_consent.json'))
    model_maybe.save_model(os.path.join(data_dir, 'model_maybe.json'))
    with open(metadata_file, 'w') as f:
        json.dump({'combined_mtime': combined_mtime}, f)
    print("Model training completed.")


if __name__ == '__main__':
    train_models()
