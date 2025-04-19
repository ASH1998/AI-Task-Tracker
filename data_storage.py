import pandas as pd
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATA_FILE = "data/activity_log.csv"
DATA_DIR = "data"

def ensure_data_dir_exists():
    """Creates the data directory if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        logging.info(f"Created directory: {DATA_DIR}")

def save_activity(timestamp, app_name, crisp_desc, main_topic, short_desc, screenshot_path):
    """Appends the activity data to the CSV file."""
    ensure_data_dir_exists()
    file_exists = os.path.isfile(DATA_FILE)

    data = {
        'Timestamp': [timestamp],
        'AppName': [app_name],
        'CrispDescription': [crisp_desc],
        'MainTopic': [main_topic],
        'ShortDescription': [short_desc],
        'ScreenshotFile': [os.path.basename(screenshot_path) if screenshot_path else None] # Store only filename
    }
    df = pd.DataFrame(data)

    try:
        if not file_exists:
            df.to_csv(DATA_FILE, index=False, encoding='utf-8')
            logging.info(f"Created new data file: {DATA_FILE}")
        else:
            # Append without writing header
            df.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8')
            logging.info(f"Appended data to {DATA_FILE}")
    except Exception as e:
        logging.error(f"Error saving data to {DATA_FILE}: {e}")

def load_activity_data():
    """Loads the activity data from the CSV file."""
    ensure_data_dir_exists()
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, encoding='utf-8')
            # Attempt to convert Timestamp column to datetime objects
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            logging.info(f"Loaded data from {DATA_FILE}")
            return df
        except pd.errors.EmptyDataError:
            logging.warning(f"Data file {DATA_FILE} is empty.")
            return pd.DataFrame(columns=['Timestamp', 'AppName', 'CrispDescription', 'MainTopic', 'ShortDescription', 'ScreenshotFile'])
        except Exception as e:
            logging.error(f"Error loading data from {DATA_FILE}: {e}")
            return pd.DataFrame(columns=['Timestamp', 'AppName', 'CrispDescription', 'MainTopic', 'ShortDescription', 'ScreenshotFile']) # Return empty df on error
    else:
        logging.info(f"Data file {DATA_FILE} does not exist yet.")
        # Return an empty DataFrame with the expected columns
        return pd.DataFrame(columns=['Timestamp', 'AppName', 'CrispDescription', 'MainTopic', 'ShortDescription', 'ScreenshotFile'])


if __name__ == '__main__':
    # Example usage
    print("Attempting to load data...")
    df_loaded = load_activity_data()
    print(f"Loaded {len(df_loaded)} records.")
    print(df_loaded.head())

    # Example save
    # now = datetime.now()
    # save_activity(now, "Example App", "Doing example task", "Example", "Short example", "data/screenshots/fake_screenshot.png")
    # print("Saved dummy record (check data/activity_log.csv)")
    # df_reloaded = load_activity_data()
    # print(f"Loaded {len(df_reloaded)} records after save.")
    # print(df_reloaded.tail())
