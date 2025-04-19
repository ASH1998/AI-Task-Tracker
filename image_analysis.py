import os
import base64
import json
import logging
from openai import AzureOpenAI, OpenAI # Use AzureOpenAI if using Azure endpoint

# Load environment variables (important: create a .env file)
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Option 1: Use Azure OpenAI
# Assumes AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME, AZURE_OPENAI_API_VERSION are in your .env file
USE_AZURE = os.getenv("USE_AZURE", "False").lower() == "true" # Set USE_AZURE=True in .env for Azure
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") # Your GPT-4 Vision deployment
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION") # Load the API version
AZURE_MODEL_NAME = os.getenv("AZURE_OPENAI_MODEL_NAME") # Load the model name (optional, for reference)

# Option 2: Use standard OpenAI API
# Assumes OPENAI_API_KEY is in your .env file
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_VISION_MODEL", "gpt-4-vision-preview") # Or relevant vision model

# --- LLM Prompt ---
LLM_PROMPT = """
based on this image of screenshot
give me three things:
1. crisp description about what the user is doing
2. Main topic (no more than 5 words)
3. short description
give this as json with keys "crisp_description", "main_topic", "short_description"
"""

# --- Client Initialization ---
client = None
if USE_AZURE:
    # Check for all required Azure variables
    if not all([AZURE_ENDPOINT, AZURE_API_KEY, AZURE_DEPLOYMENT_NAME, AZURE_API_VERSION]):
        logging.error("Azure environment variables (ENDPOINT, API_KEY, DEPLOYMENT_NAME, API_VERSION) not set.")
        # Potentially raise an error or exit
    else:
        try:
            client = AzureOpenAI(
                api_key=AZURE_API_KEY,
                api_version=AZURE_API_VERSION, # Use the specific API version from .env
                azure_endpoint=AZURE_ENDPOINT
            )
            logging.info(f"Using Azure OpenAI client. Endpoint: {AZURE_ENDPOINT}, Deployment: {AZURE_DEPLOYMENT_NAME}, API Version: {AZURE_API_VERSION}")
        except Exception as e:
            logging.error(f"Failed to initialize Azure OpenAI client: {e}")
else:
    if not OPENAI_API_KEY:
        logging.error("OPENAI_API_KEY environment variable not set.")
        # Potentially raise an error or exit
    else:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            logging.info("Using standard OpenAI client.")
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI client: {e}")

# Function to encode the image
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logging.error(f"Error encoding image {image_path}: {e}")
        return None

def analyze_screenshot(image_path):
    """Sends the screenshot to the LLM and returns the analysis."""
    if not client:
        logging.error("LLM client not initialized. Cannot analyze image.")
        return None

    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return None

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": LLM_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    }
                }
            ]
        }
    ]

    try:
        logging.info(f"Sending request to LLM for image: {os.path.basename(image_path)}")
        if USE_AZURE:
            # test just to see if it works for text only
            messages = [{"role": "user", "content": LLM_PROMPT}]
            
            
            response = client.chat.completions.create(
                model=AZURE_DEPLOYMENT_NAME, # Use deployment name for Azure
                messages=messages,
                max_tokens=300,
                # Consider adding response_format={"type": "json_object"} if API version supports it
            )
        else:
             response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=300,
                # Consider adding response_format={"type": "json_object"} if API version supports it
            )

        analysis_content = response.choices[0].message.content
        print(analysis_content)
        logging.info("Received LLM response.")
        logging.debug(f"LLM Raw Response: {analysis_content}")

        # Attempt to parse the JSON response
        try:
            # Clean potential markdown code fences
            if analysis_content.startswith("```json"):
                analysis_content = analysis_content.strip("```json").strip()
            elif analysis_content.startswith("```"):
                 analysis_content = analysis_content.strip("```").strip()

            analysis_json = json.loads(analysis_content)
            # Validate expected keys
            if all(k in analysis_json for k in ["crisp_description", "main_topic", "short_description"]):
                 return analysis_json
            else:
                logging.warning(f"LLM response JSON missing expected keys: {analysis_content}")
                # Fallback: return raw content if JSON parsing/validation fails but content exists
                return {"error": "Invalid JSON structure", "raw_content": analysis_content}

        except json.JSONDecodeError as json_err:
            logging.error(f"Failed to parse LLM response as JSON: {json_err}")
            logging.error(f"Raw response content: {analysis_content}")
            return {"error": "JSONDecodeError", "raw_content": analysis_content} # Return raw content on error

    except Exception as e:
        logging.error(f"Error calling LLM API: {e}")
        # Check for specific API errors if needed (e.g., authentication, rate limits)
        # Updated logging to show the deployment name used
        if "invalid_request_error" in str(e) and "does not support image input" in str(e):
             logging.error(f"Model deployment '{AZURE_DEPLOYMENT_NAME if USE_AZURE else OPENAI_MODEL}' might not support vision or check API version/endpoint.")
        return None


if __name__ == '__main__':
    # Example usage (requires a sample screenshot)
    # 1. Run screenshot_capture.py first to generate a screenshot
    # 2. Make sure .env is configured with your API keys/endpoint
    # 3. Update the path below if needed

    # Find a sample screenshot file (replace with actual logic if needed)
    screenshot_dir = "data/screenshots"
    sample_screenshot = None
    if os.path.exists(screenshot_dir):
        files = [os.path.join(screenshot_dir, f) for f in os.listdir(screenshot_dir) if f.endswith(".png")]
        if files:
            sample_screenshot = max(files, key=os.path.getctime) # Get the latest screenshot

    if sample_screenshot and os.path.exists(sample_screenshot):
        print(f"Analyzing sample screenshot: {sample_screenshot}")
        analysis = analyze_screenshot(sample_screenshot)
        if analysis:
            print("Analysis Result:")
            print(json.dumps(analysis, indent=2))
        else:
            print("Failed to get analysis.")
    else:
        print("No sample screenshot found in data/screenshots. Run screenshot_capture.py first.")
        print("Ensure your .env file is correctly configured with API keys/endpoints.")

