import os
import csv
import pandas as pd
from datetime import datetime

import requests
from sklearn.model_selection import train_test_split
import xgboost as xgb
from sklearn.metrics import mean_absolute_error
import hashlib

data_dir = '/data/'

feature_cols = [
    "Delta",
    "Category_enc",
    "Usergroup",
    "Prediction_lag1",
    "Consent_lag1",
    "Cancelled",
    "Weekday"
]

def get_event_info(event_id):
    # fetch from spzroenkhausen.bplaced.net/api/v0/events/{event_id}?token={API_TOKEN}
    fetch_url = f"https://spzroenkhausen.bplaced.net/api/v0/events/{event_id}?api_token={os.getenv('API_TOKEN')}"
    event_info = requests.get(fetch_url)
    if event_info.status_code == 200:
        return event_info.json()
    else:
        print(f"Failed to fetch event info for {event_id}: {event_info.status_code}")
        return None

def predict_next(df, model_pred, model_consent, feature_cols):
    next_df = pd.DataFrame({
        "Delta": [df["Delta"].values[0] + 1] if df["Delta"].values[0] <= -1 else [0],
        "Category_enc": [df["Category_enc"].values[0]],
        "Usergroup": [df["Usergroup"].values[0]],
        "Cancelled": [df["Cancelled"].values[0]],
        "Prediction_lag1": [df["Prediction"].values[0]],
        "Consent_lag1": [df["Consent"].values[0]],
        "Weekday": [df["Weekday"].values[0]]
    })

    next_df["Prediction"] = model_pred.predict(next_df[feature_cols])
    next_df["Consent"] = model_consent.predict(next_df[feature_cols])

    return next_df
    
if __name__ == "__main__":

    event_id = os.getenv('EVENT_ID')
    if not event_id:
        print("EVENT_ID is not set in the environment variables.")
        exit(1)

    # print token
    api_token = os.getenv('API_TOKEN')
    if not api_token:
        print("API_TOKEN is not set in the environment variables.")
        exit(1)
    else:
        print(f"Using API_TOKEN: {api_token}")
    
    processed_files = 0

    # calc checksum over all csv files in data_dir
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv') and not f.__contains__('-processed')]
    checksum = hashlib.sha256()
    for filename in sorted(csv_files):
        file_path = os.path.join(data_dir, filename)
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                checksum.update(chunk)
    print("Combined CSV checksum:", checksum.hexdigest())
    # check if checksum file exists
    checksum_file_path = os.path.join(data_dir, 'checksum.txt')
    if os.path.exists(checksum_file_path):
        with open(checksum_file_path, 'r') as f:
            existing_checksum = f.read().strip()
        if existing_checksum == checksum.hexdigest():
            changes = False
            print("Checksum has not changed, skipping processing.")
        else:
            changes = True
            print("Checksum has changed, processing new files.")
    else:
        changes = True
        print("Checksum file does not exist, processing all files.")
    # write checksum to file
    with open(checksum_file_path, 'w') as f:
        f.write(checksum.hexdigest())
    
    if changes:
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv') and not filename.__contains__('-processed'):
                file_path = os.path.join(data_dir, filename)
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    # get the event_id from the filename
                    event_id = filename.split('-')[0]
                    print(f"Processing file for event_id: {event_id}")
                    # get event info
                    event_info = get_event_info(event_id)

                    # check if processed file already exists
                    output_file_path = os.path.join(data_dir, f"{event_id}-processed.csv")
                    if os.path.exists(output_file_path):
                        print(f"Processed file already exists for event {event_id}. Skipping file: {file_path}")
                        continue

                    if event_info and (event_info.get('Evaluated') is True
                        or event_info.get('State') == 3):
                        if event_info.get('Evaluated') is True:
                            print(f"Event {event_id} is evaluated. Processing file: {file_path}")
                        elif event_info.get('State') == 3:
                            print(f"Event {event_id} was cancelled. Processing file: {file_path}")
                        
                        # get event date and time to calc delta
                        event_date = event_info.get('Date')
                        event_time = event_info.get('Begin')

                        if not event_date or not event_time:
                            print(f"Missing date or time for event {event_id}. Skipping file: {file_path}")
                            continue

                        event_datetime = f"{event_date} {event_time}"

                        #convert csv to dataframe, catch errors
                        try:
                            df = pd.read_csv(file_path, parse_dates=[0])
                            df.columns = [col.strip() for col in df.columns]  # strip whitespace from column names
                            df['Delta'] = - (pd.to_datetime(event_datetime) - df.iloc[:, 0]).dt.total_seconds() / 3600 # convert to hours
                            df['Category'] = event_info.get('Category', 'Unknown')
                            df['Usergroup'] = event_info.get('Usergroup_ID', 'Unknown')
                            df['Event_ID'] = event_id
                            df['Cancelled'] = event_info.get('State') == 3
                            df['Weekday'] = datetime.strptime(event_datetime, '%Y-%m-%d %H:%M:%S').weekday()

                            # if prediction is 0, data is not valid, remove those rows
                            df = df[df.iloc[:, 1] != 0]

                        except Exception as e:
                            print(f"Error processing file {file_path}: {e}")
                            continue

                        df.columns = [col.strip() for col in df.columns]  # strip whitespace from column names
                        # save dataframe to csv
                        output_file_path = os.path.join(data_dir, f"{event_id}-processed.csv")
                        try:
                            df.to_csv(output_file_path, index=False)
                            print(f"Processed file saved: {output_file_path}")
                            processed_files += 1
                        except Exception as e:
                            print(f"Error saving processed file {output_file_path}: {e}")
                    else:
                        print(f"Event {event_id} is not evaluated or event info is missing. Skipping file: {file_path}")
                        continue

                    # remove original file
                    # try:
                    #     os.remove(file_path)
                    #     print(f"Removed original file: {file_path}")
                    # except Exception as e:
                    #     print(f"Error removing original file {file_path}: {e}")
    
    print("Preprocessing completed, processed files:", processed_files)

    # read all processed files and combine them into one dataframe
    processed_files = [f for f in os.listdir(data_dir) if f.endswith('-processed.csv')]
    combined_df = pd.DataFrame()
    for processed_file in processed_files:
        file_path = os.path.join(data_dir, processed_file)
        try:
            df = pd.read_csv(file_path)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        except Exception as e:
            print(f"Error reading processed file {file_path}: {e}")
    # save combined dataframe to csv
    combined_file_path = os.path.join(data_dir, 'combined.csv')
    try:
        # remove old combined file if it exists
        if os.path.exists(combined_file_path):
            os.remove(combined_file_path)
            print(f"Removed old combined processed file: {combined_file_path}")
        # save new combined dataframe
        combined_df.to_csv(combined_file_path, index=False)
        print(f"Combined processed file saved: {combined_file_path}")
    except Exception as e:
        print(f"Error saving combined processed file {combined_file_path}: {e}")

    cat_type = pd.api.types.CategoricalDtype(categories=combined_df["Category"].unique(), ordered=True)

    if (
        processed_files != 0
        or not os.path.exists(os.path.join(data_dir, 'model_prediction.json'))
        or not os.path.exists(os.path.join(data_dir, 'model_consent.json'))
    ):

        # Daten einlesen
        df = combined_df

        df = df.sort_values(by=["Event_ID", "Delta"])

        # create Lag-Features
        df["Prediction_lag1"] = df.groupby("Event_ID")["Prediction"].shift(1)

        df["Consent_lag1"] = df.groupby("Event_ID")["Consent"].shift(1)

        # Kategorie als numerisch kodieren
        df["Category_enc"] = df["Category"].astype(cat_type).cat.codes

        # Beispiel: 80% Training, 20% Test
        X = df[feature_cols]
        y_pred = df["Prediction"]
        y_consent = df["Consent"]

        X_train_p, X_test_p, y_train_p, y_test_p = train_test_split(
            X, y_pred, test_size=0.2, random_state=42
        )

        X_train_c, X_test_c, y_train_c, y_test_c = train_test_split(
            X, y_consent, test_size=0.2, random_state=42
        )

        model_pred = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
        model_pred.fit(X_train_p, y_train_p)

        model_consent = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42)
        model_consent.fit(X_train_c, y_train_c)

        # save the models
        model_pred.save_model(os.path.join(data_dir, 'model_prediction.json'))
        model_consent.save_model(os.path.join(data_dir, 'model_consent.json'))

    # y_pred_pred = model_pred.predict(X_test_p)
    # y_pred_consent = model_consent.predict(X_test_c)

    # mae_pred = mean_absolute_error(y_test_p, y_pred_pred)
    # mae_consent = mean_absolute_error(y_test_c, y_pred_consent)

    # print(f"MAE Prediction: {mae_pred:.2f}")
    # print(f"MAE Consent: {mae_consent:.2f}")

    # Load the models
    model_pred = xgb.XGBRegressor()
    model_pred.load_model(os.path.join(data_dir, 'model_prediction.json'))
    model_consent = xgb.XGBRegressor()
    model_consent.load_model(os.path.join(data_dir, 'model_consent.json'))

    # event_id = '498'
    event_id = os.getenv('EVENT_ID')

    cat_type = pd.api.types.CategoricalDtype(categories=combined_df["Category"].unique(), ordered=True)
    
    probe_files = [f for f in os.listdir(data_dir) if f.startswith(f'{event_id}') and f.endswith('.csv') and f != f'{event_id}-processed.csv']
    if not probe_files:
        print(f"No probe file found for event_id {event_id}.")
        exit(1)
    df_probe = pd.DataFrame()
    
    print(f"Found {len(probe_files)} probe files for event_id {event_id}.")

    for probe_file in probe_files:
        probe_file_path = os.path.join(data_dir, probe_file)
        df_single = pd.read_csv(probe_file_path, parse_dates=[0])
        df_probe = pd.concat([df_probe, df_single])
    df_probe.columns = [col.strip() for col in df_probe.columns]  # strip whitespace from column names

    event_info = get_event_info(event_id)
    
    event_date = event_info.get('Date')
    event_time = event_info.get('Begin')
    event_datetime = f"{event_date} {event_time}"

    df_probe["Delta"] = - (pd.to_datetime(event_datetime) - pd.to_datetime(df_probe.iloc[:, 0])).dt.total_seconds() / 3600  # convert to hours
    df_probe["Category"] = event_info.get('Category', 'Unknown')
    df_probe["Usergroup"] = event_info.get('Usergroup_ID', 'Unknown')
    df_probe["Cancelled"] = event_info.get('State') == 3
    df_probe["Prediction_lag1"] = df_probe["Prediction"].shift(1)
    df_probe["Consent_lag1"] = df_probe["Consent"].shift(1)
    df_probe["Category_enc"] = df_probe["Category"].astype(cat_type).cat.codes
    df_probe["Weekday"] = datetime.strptime(event_datetime, '%Y-%m-%d %H:%M:%S').weekday()

    # Ensure the dataframe is sorted by Delta
    df_probe = df_probe.sort_values(by=["Delta"]).reset_index(drop=True)

    latest_delta = df_probe["Delta"].max()

    while df_probe["Delta"].iloc[-1] < 0:
        
        # Predict next values
        df_probe_next = predict_next(df_probe.tail(1), model_pred, model_consent, feature_cols)

        print(df_probe_next[["Delta", "Prediction", "Consent"]])

        # Append the new prediction to the dataframe
        df_probe = pd.concat([df_probe, df_probe_next], ignore_index=True)

    # print("Final predictions:")
    # print(df_probe[["Delta", "Prediction", "Consent"]])

    # plot the results and save the figure, draw a line vertically where prediction starts,
    # shorten df to the last 7 days of data
    df_probe = df_probe[df_probe["Delta"] >= -168]  # last 7 days (168 hours)
    import matplotlib.pyplot as plt
    plt.figure(figsize=(12, 6))
    plt.plot(df_probe["Delta"], df_probe["Prediction"], label="Prediction", marker='o')
    plt.plot(df_probe["Delta"], df_probe["Consent"], label="Consent", marker='x')
    plt.axvline(x=latest_delta, color='r', linestyle='--', label='Latest Delta')
    plt.xlabel("Delta (hours)")
    plt.ylabel("Values")
    plt.title("Predictions and Consent Over Time")
    plt.legend()
    plt.grid()
    plt.savefig(os.path.join(data_dir, f'{event_id}.png'))

    # plot feature importance of the model
    xgb.plot_importance(model_pred, title='Feature Importance for Prediction Model')
    plt.savefig(os.path.join(data_dir, 'feature_importance_prediction.png'))
    
    xgb.plot_importance(model_consent, title='Feature Importance for Consent Model')
    plt.savefig(os.path.join(data_dir, 'feature_importance_consent.png'))

    # print the feature importance
    print("Feature importance for Prediction Model:")
    for i, (feature, score) in enumerate(zip(model_pred.get_booster().feature_names, model_pred.feature_importances_)):
        print(f"{i+1}. {feature}: {score:.4f}")
