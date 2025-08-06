from preprocess import preprocess_data
from train_models import train_models
from predict import run_prediction
import os

if __name__ == "__main__":
    preprocess_data()
    train_models()
    event_id = os.getenv('EVENT_ID')
    if event_id:
        run_prediction(event_id)
    else:
        print("EVENT_ID is not set in the environment variables. Prediction skipped.")
