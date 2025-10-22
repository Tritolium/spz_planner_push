import os
from datetime import datetime

import pandas as pd
import xgboost as xgb
import matplotlib.pyplot as plt

from utils import data_dir, feature_cols, get_event_info


def predict_next(df: pd.DataFrame, model_pred, model_consent, model_maybe):
    next_df = pd.DataFrame(
        {
            "Delta": [df["Delta"].values[0] + 1]
            if df["Delta"].values[0] <= -1
            else [0],
            "Category_enc": [df["Category_enc"].values[0]],
            "Usergroup": [df["Usergroup"].values[0]],
            "Cancelled": [df["Cancelled"].values[0]],
            "Prediction_lag1": [df["Prediction"].values[0]],
            "Consent_lag1": [df["Consent"].values[0]],
            "Maybe_lag1": [df["Maybe"].values[0]],
            "Weekday": [df["Weekday"].values[0]],
        }
    )
    # Convert all feature columns to numeric to avoid dtype issues
    for col in feature_cols:
        next_df[col] = pd.to_numeric(next_df[col], errors="coerce")
    next_df["Prediction"] = model_pred.predict(next_df[feature_cols])
    next_df["Consent"] = model_consent.predict(next_df[feature_cols])
    next_df["Maybe"] = model_maybe.predict(next_df[feature_cols])
    return next_df


def run_prediction(event_id: str):
    model_pred_path = os.path.join(data_dir, 'model_prediction.json')
    model_consent_path = os.path.join(data_dir, 'model_consent.json')
    model_maybe_path = os.path.join(data_dir, 'model_maybe.json')
    if not (
        os.path.exists(model_pred_path)
        and os.path.exists(model_consent_path)
        and os.path.exists(model_maybe_path)
    ):
        print("Models not found; run training first.")
        return None

    combined_file_path = os.path.join(data_dir, 'combined.csv')
    if not os.path.exists(combined_file_path):
        print("Combined dataset not found; run preprocessing first.")
        return None

    model_pred = xgb.XGBRegressor()
    model_pred.load_model(model_pred_path)
    model_consent = xgb.XGBRegressor()
    model_consent.load_model(model_consent_path)
    model_maybe = xgb.XGBRegressor()
    model_maybe.load_model(model_maybe_path)

    combined_df = pd.read_csv(combined_file_path)
    cat_type = pd.api.types.CategoricalDtype(
        categories=combined_df["Category"].unique(), ordered=True
    )

    probe_files = [
        f
        for f in os.listdir(data_dir)
        if f.startswith(f"{event_id}") and f.endswith('.csv') and f != f"{event_id}-processed.csv"
    ]
    if not probe_files:
        print("No probe file found for the event.")
        return None

    df_probe = pd.DataFrame()
    for probe_file in probe_files:
        probe_file_path = os.path.join(data_dir, probe_file)
        cleancsvfile(probe_file_path)
        df_single = pd.read_csv(probe_file_path, parse_dates=[0])
        df_probe = pd.concat([df_probe, df_single])
    df_probe.columns = [col.strip() for col in df_probe.columns]

    # Ensure numeric columns have proper dtype
    for col in ["Prediction", "Consent", "Maybe"]:
        df_probe[col] = pd.to_numeric(df_probe[col], errors="coerce")

    event_info = get_event_info(event_id)
    event_date = event_info.get('Date')
    event_time = event_info.get('Begin')
    event_datetime = f"{event_date} {event_time}"

    df_probe["Delta"] = -(
        pd.to_datetime(event_datetime) - pd.to_datetime(df_probe.iloc[:, 0])
    ).dt.total_seconds() / 3600
    df_probe["Category"] = event_info.get('Category', 'Unknown')
    df_probe["Usergroup"] = event_info.get('Usergroup_ID', 'Unknown')
    df_probe["Cancelled"] = event_info.get('State') == 3
    df_probe["Prediction_lag1"] = df_probe["Prediction"].shift(1)
    df_probe["Consent_lag1"] = df_probe["Consent"].shift(1)
    df_probe["Maybe_lag1"] = df_probe["Maybe"].shift(1)
    df_probe["Category_enc"] = df_probe["Category"].astype(cat_type).cat.codes
    df_probe["Weekday"] = datetime.strptime(
        event_datetime, '%Y-%m-%d %H:%M:%S'
    ).weekday()

    df_probe = df_probe.sort_values(by=["Delta"]).reset_index(drop=True)
    latest_delta = df_probe["Delta"].max()

    while df_probe["Delta"].iloc[-1] < 0:
        df_probe_next = predict_next(df_probe.tail(1), model_pred, model_consent, model_maybe)
        df_probe = pd.concat([df_probe, df_probe_next], ignore_index=True)

    df_probe = df_probe[df_probe["Delta"] >= -168]

    plt.figure(figsize=(12, 6))
    plt.plot(df_probe["Delta"], df_probe["Prediction"], label="Prediction", marker='o')
    plt.plot(df_probe["Delta"], df_probe["Consent"], label="Consent", marker='x')
    plt.plot(df_probe["Delta"], df_probe["Maybe"], label="Maybe", marker='s')
    plt.axvline(x=latest_delta, color='r', linestyle='--', label='Latest Delta')
    plt.xlabel("Delta (hours)")
    plt.ylabel("Values")
    plt.title("Predictions and Consent Over Time")
    plt.legend()
    plt.grid()
    plt.savefig(os.path.join(data_dir, f"{event_id}.png"))

    xgb.plot_importance(model_pred, title='Feature Importance for Prediction Model')
    plt.savefig(os.path.join(data_dir, 'feature_importance_prediction.png'))

    xgb.plot_importance(model_consent, title='Feature Importance for Consent Model')
    plt.savefig(os.path.join(data_dir, 'feature_importance_consent.png'))

    xgb.plot_importance(model_maybe, title='Feature Importance for Maybe Model')
    plt.savefig(os.path.join(data_dir, 'feature_importance_maybe.png'))

    result_df = df_probe[["Delta", "Prediction", "Consent", "Maybe"]].copy()
    for col in ["Prediction", "Consent", "Maybe"]:
        result_df[col] = result_df[col].round().astype(int)
    return result_df

def cleancsvfile(filepath: str):
    df = pd.read_csv(filepath)
    df.columns = df.columns.str.strip()
    # remove all rows where Prediction is 0
    df = df[df['Prediction'] != 0]
    df.to_csv(filepath, index=False)

if __name__ == '__main__':
    EVENT_ID = os.getenv('EVENT_ID')
    if not EVENT_ID:
        print("EVENT_ID is not set in the environment variables.")
    else:
        run_prediction(EVENT_ID)
