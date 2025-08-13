import os
import requests

data_dir = '/data/'

feature_cols = [
    "Delta",
    "Category_enc",
    "Usergroup",
    "Prediction_lag1",
    "Consent_lag1",
    "Cancelled",
    "Weekday",
]

def get_event_info(event_id: str):
    """Fetch event metadata from the remote API."""
    fetch_url = (
        f"https://spzroenkhausen.bplaced.net/api/v0/events/{event_id}?api_token="
        f"{os.getenv('API_TOKEN')}"
    )
    event_info = requests.get(fetch_url)
    if event_info.status_code == 200:
        return event_info.json()
    print(f"Failed to fetch event info: {event_info.status_code}")
    return None
