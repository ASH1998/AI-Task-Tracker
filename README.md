# AI-Task-Tracker

AI-Task-Tracker is an automated productivity and activity tracking tool that uses screenshots, window titles, and AI-powered analysis to log and summarize your computer activity. It leverages OpenAI (or Azure OpenAI) models to generate concise descriptions and normalized topics for each activity, helping you analyze how you spend your time.

## Features

- **Automated Screenshot Capture:** Periodically captures screenshots of your desktop.
- **Active Window Detection:** Logs the currently active application/window.
- **AI-Powered Analysis:** Uses LLMs to generate crisp descriptions, main topics, and short summaries for each activity.
- **Topic Normalization:** Ensures consistent topic naming using an LLM-based normalizer.
- **Data Logging:** Stores activity data in a CSV file, including timestamps, app names, topics, and screenshot references.
- **Streamlit Dashboard:** Visualizes your activity data, including time spent per topic, activity counts, and screenshot viewer.

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/yourusername/AI-Task-Tracker.git
   cd AI-Task-Tracker
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   - Copy `.env.example` to `.env` (if provided) or create a `.env` file.
   - Set your OpenAI or Azure OpenAI credentials and configuration in `.env`:
     ```
     USE_AZURE=True
     AZURE_OPENAI_ENDPOINT=...
     AZURE_OPENAI_API_KEY=...
     AZURE_OPENAI_DEPLOYMENT_NAME=...
     AZURE_OPENAI_API_VERSION=...
     AZURE_OPENAI_MODEL_NAME=...
     # Or for OpenAI:
     OPENAI_API_KEY=...
     ```

4. **Run the tracker:**
   ```sh
   python main.py
   ```
   This will start periodic activity tracking and logging.

5. **View your activity dashboard:**
   ```sh
   streamlit run app.py
   ```
   Open the provided local URL in your browser to explore your activity data.

## File Structure

- `main.py` - Main tracking loop.
- `image_analysis.py` - Handles screenshot analysis using LLMs.
- `topic_normalizer.py` - Normalizes topics using LLMs.
- `screenshot_capture.py` - Captures and saves screenshots.
- `data_storage.py` - Handles saving/loading activity data.
- `app.py` - Streamlit dashboard for data visualization.
- `utils.py` - Utility functions (e.g., active window detection).
- `data/` - Stores activity logs and screenshots.

## Notes

- Screenshots and logs are saved in the `data/` directory.
- Make sure your API keys are kept secure and not shared publicly.
- The tool is cross-platform but screenshot and window detection may have OS-specific limitations.

## License

This project is licensed under the [Apache 2.0 License](LICENSE).

---