import os
import logging
from openai import AzureOpenAI, OpenAI
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Use the same client configuration as in image_analysis.py
USE_AZURE = os.getenv("USE_AZURE", "False").lower() == "true"
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") 
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

# Standard OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo") # Text model (not vision)

# --- LLM Prompt ---
NORMALIZE_PROMPT = """
You are a topic normalizer. Your task is to normalize the given topic to a consistent format.
For example:
- "working with vs code" and "coding on vs code" should both be normalized to "Visual Studio Code"
- "python programming" and "coding in python" should both be normalized to "Python Programming"

Return only the normalized topic as plain text, without any additional explanations or formatting.

Topic to normalize: {topic}
"""

# --- Client Initialization ---
client = None
if USE_AZURE:
    if not all([AZURE_ENDPOINT, AZURE_API_KEY, AZURE_DEPLOYMENT_NAME, AZURE_API_VERSION]):
        logging.error("Azure environment variables not set for topic normalizer.")
    else:
        try:
            client = AzureOpenAI(
                api_key=AZURE_API_KEY,
                api_version=AZURE_API_VERSION,
                azure_endpoint=AZURE_ENDPOINT
            )
            logging.info("Topic normalizer using Azure OpenAI client.")
        except Exception as e:
            logging.error(f"Failed to initialize Azure OpenAI client for topic normalizer: {e}")
else:
    if not OPENAI_API_KEY:
        logging.error("OPENAI_API_KEY environment variable not set for topic normalizer.")
    else:
        try:
            client = OpenAI(api_key=OPENAI_API_KEY)
            logging.info("Topic normalizer using standard OpenAI client.")
        except Exception as e:
            logging.error(f"Failed to initialize OpenAI client for topic normalizer: {e}")

@lru_cache(maxsize=100)  # Cache results to avoid repeated API calls for same topics
def normalize_topic(topic):
    """Normalizes a topic using LLM to ensure consistency."""
    if not client:
        logging.error("LLM client not initialized. Cannot normalize topic.")
        return topic  # Return original topic if client is not available
    
    if not topic or not isinstance(topic, str):
        return "Unknown"
    
    try:
        logging.info(f"Normalizing topic: '{topic}'")
        messages = [
            {
                "role": "system",
                "content": "You are a topic normalizer assistant. Respond only with the normalized topic."
            },
            {
                "role": "user",
                "content": NORMALIZE_PROMPT.format(topic=topic)
            }
        ]
        
        if USE_AZURE:
            response = client.chat.completions.create(
                model=AZURE_DEPLOYMENT_NAME,
                messages=messages,
                max_tokens=50,
                temperature=0.1  # Low temperature for consistent results
            )
        else:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=50,
                temperature=0.1
            )
            
        normalized_topic = response.choices[0].message.content.strip()
        logging.info(f"Normalized '{topic}' to '{normalized_topic}'")
        return normalized_topic
        
    except Exception as e:
        logging.error(f"Error normalizing topic: {e}")
        return topic  # Return original topic on error
        
if __name__ == '__main__':
    # Test the topic normalizer
    test_topics = [
        "working with vs code", 
        "coding on vs code",
        "python programming",
        "coding in python",
        "azure openai integration",
        "setting up azure api"
    ]
    
    for topic in test_topics:
        normalized = normalize_topic(topic)
        print(f"Original: '{topic}' → Normalized: '{normalized}'")
