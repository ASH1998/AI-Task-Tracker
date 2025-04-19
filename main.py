import time
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

from screenshot_capture import take_screenshot
from image_analysis import analyze_screenshot
from data_storage import save_activity
from utils import get_active_window_title

# --- Load Configuration from .env ---
load_dotenv()
TRACKING_INTERVAL_SECONDS = int(os.getenv('TRACKING_INTERVAL_SECONDS', 120))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
RETRY_DELAY_SECONDS = int(os.getenv('RETRY_DELAY_SECONDS', 10))

# --- Logging Setup ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
log_file = os.path.join(LOG_DIR, f"tracker_{datetime.now().strftime('%Y%m%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler() # Also print logs to console
    ]
)

def run_tracker_iteration():
    """Performs one iteration of the tracking loop."""
    logging.info("--- Starting tracking iteration ---")
    timestamp = datetime.now()
    screenshot_path = None
    analysis_result = None
    active_window = "Unknown"

    # 1. Get Active Window Title
    try:
        active_window = get_active_window_title()
        logging.info(f"Active window: {active_window}")
    except Exception as e:
        logging.error(f"Failed to get active window: {e}")
        # Continue anyway, but log the error

    # 2. Take Screenshot (with retries)
    for attempt in range(MAX_RETRIES):
        try:
            screenshot_path = take_screenshot()
            if screenshot_path:
                logging.info(f"Screenshot successful: {screenshot_path}")
                break # Exit retry loop on success
            else:
                logging.warning(f"Screenshot attempt {attempt + 1} failed. Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
        except Exception as e:
            logging.error(f"Exception during screenshot attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                 logging.error("Max screenshot retries reached. Skipping analysis for this iteration.")

    if not screenshot_path:
        logging.error("Failed to take screenshot after multiple attempts.")
        # Optionally save a record indicating screenshot failure
        # save_activity(timestamp, active_window, "Screenshot Failed", "Error", "Could not capture screen", None)
        return # End iteration if screenshot failed

    # 3. Analyze Screenshot (with retries)
    for attempt in range(MAX_RETRIES):
        try:
            analysis_result = analyze_screenshot(screenshot_path)
            if analysis_result:
                if "error" in analysis_result:
                     logging.warning(f"LLM analysis attempt {attempt + 1} resulted in an error: {analysis_result.get('error')}. Raw: {analysis_result.get('raw_content')}")
                     # Decide if this error is retryable or permanent
                     if analysis_result.get('error') == "JSONDecodeError" and attempt < MAX_RETRIES - 1:
                         logging.info(f"Retrying analysis in {RETRY_DELAY_SECONDS}s...")
                         time.sleep(RETRY_DELAY_SECONDS)
                         continue # Retry if JSON decode error
                     else:
                         # Non-retryable error or max retries reached, save error state
                         save_activity(timestamp, active_window, "Analysis Error", "Error", analysis_result.get('raw_content', 'Analysis failed'), screenshot_path)
                         analysis_result = None # Ensure we don't proceed with bad data
                         break # Exit retry loop
                else:
                    logging.info("LLM analysis successful.")
                    break # Exit retry loop on success
            else:
                logging.warning(f"LLM analysis attempt {attempt + 1} returned None. Retrying in {RETRY_DELAY_SECONDS}s...")
                time.sleep(RETRY_DELAY_SECONDS)
        except Exception as e:
            logging.error(f"Exception during analysis attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                logging.error("Max analysis retries reached.")
                save_activity(timestamp, active_window, "Analysis Failed", "Error", f"Exception during analysis: {e}", screenshot_path)
                analysis_result = None # Ensure we don't proceed

    # 4. Save Data
    if analysis_result and "error" not in analysis_result:
        try:
            save_activity(
                timestamp=timestamp,
                app_name=active_window,
                crisp_desc=analysis_result.get("crisp_description", "N/A"),
                main_topic=analysis_result.get("main_topic", "N/A"),
                short_desc=analysis_result.get("short_description", "N/A"),
                screenshot_path=screenshot_path
            )
            logging.info("Activity data saved successfully.")
        except Exception as e:
            logging.error(f"Failed to save activity data: {e}")
    elif not analysis_result:
         logging.warning("No valid analysis result obtained, skipping save for this iteration (error should have been logged/saved previously).")
    # else: analysis_result had an error, which was already saved by the retry logic

    # 5. Optional: Clean up old screenshots (implement if needed)
    # cleanup_old_screenshots(SCREENSHOT_DIR, keep_days=7)

    logging.info("--- Finished tracking iteration ---")


def main():
    """Main loop for the activity tracker."""
    logging.info("Starting AI Task Tracker...")
    logging.info(f"Tracking interval set to {TRACKING_INTERVAL_SECONDS} seconds.")
    logging.info("Ensure your .env file is configured with API keys/endpoints.")

    while True:
        try:
            run_tracker_iteration()
            logging.info(f"Sleeping for {TRACKING_INTERVAL_SECONDS} seconds...")
            time.sleep(TRACKING_INTERVAL_SECONDS)
        except KeyboardInterrupt:
            logging.info("Tracker stopped by user (KeyboardInterrupt).")
            break
        except Exception as e:
            logging.critical(f"Unhandled exception in main loop: {e}", exc_info=True)
            # Decide whether to continue or exit on critical errors
            logging.info("Attempting to continue after 60 seconds...")
            time.sleep(60)


if __name__ == "__main__":
    main()
