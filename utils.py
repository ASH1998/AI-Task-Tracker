import pygetwindow as gw
import platform
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_active_window_title():
    """Gets the title of the currently active window."""
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            return active_window.title
        else:
            # Handle cases where there might not be an active window (e.g., background script)
            return "No active window found"
    except Exception as e:
        logging.error(f"Error getting active window title: {e}")
        # Fallback for specific platforms if needed, or return a default
        if platform.system() == "Linux":
             logging.warning("pygetwindow might have limitations on Linux Wayland.")
        return "Error getting window title"

if __name__ == '__main__':
    # Example usage
    title = get_active_window_title()
    print(f"Active window: {title}")
