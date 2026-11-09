
import os
import logging
from dotenv import load_dotenv
from google import genai

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    logger.error("Gemini API key not found in .env file.")
else:
    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents="Explain Information Assurance in two simple sentences."
        )

        print("Gemini API connected successfully!")
        print("\nGemini Response:\n")
        print(response.text)

    except Exception:
        logger.exception("Gemini API connection failed.")
