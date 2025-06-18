
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
        GROQ_API_KEY = os.getenv("GROQ_API_KEY","")
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY",'')
        country = os.getenv("COUNTRY", "Romania")
        city_start = os.getenv("CITY_START", "Cluj Napoca")
        city_end = os.getenv("CITY_END", "Cluj Napoca")
        duration = int(os.getenv("DURATION", 10))
        month = os.getenv("MONTH", "July")
        composition = os.getenv("COMPOSITION", "a family with young children")
        location_val = os.getenv("LOCATION_VAL" , "False").lower() == 'true'
        max_km_dist_per_day = int(os.getenv("MAX_KM_DIST_PER_DAY", "150"))

    return Config