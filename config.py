
from dotenv import load_dotenv
import os

def get_config():
    """
    Load configuration from environment variables.
    """
    load_dotenv()
    class Config:
        MODEL_NAME = os.getenv("MODEL_NAME", "llama3")
        OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY",'')
        country = os.getenv("COUNTRY", "Romania")
        city_start = os.getenv("CITY_START", "Cluj Napoca")
        city_end = os.getenv("CITY_END", "Cluj Napoca")
        duration = int(os.getenv("DURATION", 10))
        month = os.getenv("MONTH", "July")
        composition = os.getenv("COMPOSITION", "a family with young children")

    return Config