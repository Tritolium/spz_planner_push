import os
import time
from typing import Dict

from preprocess import preprocess_data
from train_models import train_models
from predict import run_prediction
from utils import data_dir

CHECK_INTERVAL = 10  # seconds

def snapshot_raw() -> Dict[str, float]:
    """Return modification times for raw CSV files."""
    return {
        f: os.path.getmtime(os.path.join(data_dir, f))
        for f in os.listdir(data_dir)
        if f.endswith('.csv') and '-processed' not in f and f != 'combined.csv'
    }


def snapshot_probe(event_id: str) -> Dict[str, float]:
    """Return modification times for probe files of a given event."""
    return {
        f: os.path.getmtime(os.path.join(data_dir, f))
        for f in os.listdir(data_dir)
        if f.startswith(event_id) and f.endswith('.csv') and '-processed' not in f
    }


def models_mtime() -> float:
    """Return the newest modification time among model files."""
    mtimes = []
    for name in ['model_prediction.json', 'model_consent.json', 'model_maybe.json']:
        path = os.path.join(data_dir, name)
        if os.path.exists(path):
            mtimes.append(os.path.getmtime(path))
    return max(mtimes) if mtimes else 0.0


def main() -> None:
    raw_state = snapshot_raw()
    combined_path = os.path.join(data_dir, 'combined.csv')
    combined_mtime = os.path.getmtime(combined_path) if os.path.exists(combined_path) else 0

    event_id = os.getenv('EVENT_ID')
    probe_state = snapshot_probe(event_id) if event_id else {}
    model_state = models_mtime()

    while True:
        time.sleep(CHECK_INTERVAL)

        # Trigger preprocessing when raw logs change
        current_raw = snapshot_raw()
        if current_raw != raw_state:
            preprocess_data()
            raw_state = current_raw
            # Update combined mtime after preprocessing
            combined_mtime = os.path.getmtime(combined_path) if os.path.exists(combined_path) else combined_mtime

        # Trigger training when combined dataset changes
        if os.path.exists(combined_path):
            current_combined_mtime = os.path.getmtime(combined_path)
            if current_combined_mtime != combined_mtime:
                train_models()
                combined_mtime = current_combined_mtime
                model_state = models_mtime()

        # Trigger prediction when probe files or models change
        if event_id:
            current_probe = snapshot_probe(event_id)
            current_model_state = models_mtime()
            if current_probe != probe_state or current_model_state != model_state:
                run_prediction(event_id)
                probe_state = current_probe
                model_state = current_model_state


if __name__ == '__main__':
    main()
