import os
import time
from typing import Dict

from preprocess import preprocess_data
from train_models import train_models
from utils import data_dir

CHECK_INTERVAL = 10  # seconds

def snapshot_raw() -> Dict[str, float]:
    """Return modification times for raw CSV files."""
    return {
        f: os.path.getmtime(os.path.join(data_dir, f))
        for f in os.listdir(data_dir)
        if f.endswith('.csv') and '-processed' not in f and f != 'combined.csv'
    }


def main() -> None:
    raw_state = snapshot_raw()
    combined_path = os.path.join(data_dir, 'combined.csv')
    combined_mtime = os.path.getmtime(combined_path) if os.path.exists(combined_path) else 0

    # Run preprocessing once if no processed files exist yet
    processed_present = any(
        f.endswith('-processed.csv') for f in os.listdir(data_dir)
    )
    if not processed_present:
        preprocess_data()
        if os.path.exists(combined_path):
            train_models()
            combined_mtime = os.path.getmtime(combined_path)

    while True:
        time.sleep(CHECK_INTERVAL)

        # Trigger preprocessing when raw logs change
        current_raw = snapshot_raw()
        if current_raw != raw_state:
            preprocess_data()
            raw_state = current_raw
            combined_mtime = os.path.getmtime(combined_path) if os.path.exists(combined_path) else combined_mtime

        # Trigger training when combined dataset changes
        if os.path.exists(combined_path):
            current_combined_mtime = os.path.getmtime(combined_path)
            if current_combined_mtime != combined_mtime:
                train_models()
                combined_mtime = current_combined_mtime


if __name__ == '__main__':
    main()
