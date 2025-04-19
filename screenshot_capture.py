from PIL import ImageGrab
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SCREENSHOT_DIR = "data/screenshots"

def take_screenshot():
    """Takes a screenshot and saves it to the specified directory."""
    try:
        # Ensure the screenshot directory exists
        if not os.path.exists(SCREENSHOT_DIR):
            os.makedirs(SCREENSHOT_DIR)
            logging.info(f"Created directory: {SCREENSHOT_DIR}")

        screenshot = ImageGrab.grab()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(SCREENSHOT_DIR, f"screenshot_{timestamp}.png")
        screenshot.save(file_path)
        logging.info(f"Screenshot saved to {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Error taking screenshot: {e}")
        return None

if __name__ == '__main__':
    # Example usage
    path = take_screenshot()
    if path:
        print(f"Screenshot taken and saved to: {path}")
    else:
        print("Failed to take screenshot.")
