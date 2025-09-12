import os
import hashlib
from datetime import datetime

import pandas as pd

from utils import data_dir, get_event_info


def preprocess_data():
    processed_files = 0

    csv_files = [
        f
        for f in os.listdir(data_dir)
        if f.endswith('.csv') and '-processed' not in f and f != 'combined.csv'
    ]
    checksum = hashlib.sha256()
    for filename in sorted(csv_files):
        file_path = os.path.join(data_dir, filename)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                checksum.update(chunk)

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
    with open(checksum_file_path, 'w') as f:
        f.write(checksum.hexdigest())

    combined_file_path = os.path.join(data_dir, 'combined.csv')

    # When no raw files changed, check if any previously skipped events
    # have since been marked evaluated so we can process them now.
    if not changes:
        for filename in csv_files:
            event_id = filename.split('-')[0]
            output_file_path = os.path.join(data_dir, f"{event_id}-processed.csv")
            if os.path.exists(output_file_path):
                continue
            event_info = get_event_info(event_id)
            if event_info and (
                event_info.get('Evaluated') is True or event_info.get('State') == 3
            ):
                changes = True
                break

    if not changes and os.path.exists(combined_file_path):
        print("Input data unchanged; combined dataset is up to date.")
        return

    if changes:
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv') and '-processed' not in filename:
                file_path = os.path.join(data_dir, filename)
                event_id = filename.split('-')[0]
                event_info = get_event_info(event_id)

                output_file_path = os.path.join(
                    data_dir, f"{event_id}-processed.csv"
                )
                if os.path.exists(output_file_path):
                    continue

                if event_info and (
                    event_info.get('Evaluated') is True
                    or event_info.get('State') == 3
                ):
                    event_date = event_info.get('Date')
                    event_time = event_info.get('Begin')
                    if not event_date or not event_time:
                        continue
                    event_datetime = f"{event_date} {event_time}"

                    try:
                        df = pd.read_csv(file_path, parse_dates=[0])
                        df.columns = [col.strip() for col in df.columns]
                        df['Delta'] = -(
                            pd.to_datetime(event_datetime) - df.iloc[:, 0]
                        ).dt.total_seconds() / 3600
                        df['Category'] = event_info.get('Category', 'Unknown')
                        df['Usergroup'] = event_info.get('Usergroup_ID', 'Unknown')
                        df['Event_ID'] = event_id
                        df['Cancelled'] = event_info.get('State') == 3
                        df['Weekday'] = datetime.strptime(
                            event_datetime, '%Y-%m-%d %H:%M:%S'
                        ).weekday()
                        df = df[df.iloc[:, 1] != 0]
                    except Exception as e:  # noqa: BLE001
                        print(f"Error processing file: {e}")
                        continue

                    try:
                        df.to_csv(output_file_path, index=False)
                        processed_files += 1
                    except Exception as e:  # noqa: BLE001
                        print(f"Error saving processed file: {e}")

    print("Preprocessing completed, processed files:", processed_files)

    processed_files = [
        f for f in os.listdir(data_dir) if f.endswith('-processed.csv')
    ]
    combined_df = pd.DataFrame()
    for processed_file in processed_files:
        file_path = os.path.join(data_dir, processed_file)
        try:
            df = pd.read_csv(file_path)
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        except Exception as e:  # noqa: BLE001
            print(f"Error reading processed file: {e}")

    try:
        if os.path.exists(combined_file_path):
            os.remove(combined_file_path)
        combined_df.to_csv(combined_file_path, index=False)
    except Exception as e:  # noqa: BLE001
        print(f"Error saving combined processed file: {e}")


if __name__ == '__main__':
    preprocess_data()
