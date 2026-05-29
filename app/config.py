from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str
    MODEL_NAME: str = "meta-llama/llama-4-scout-17b-16e-instruct" #"llama-3.3-70b-versatile"
    TELEGRAM_TOKEN: str
    SUPERVISOR_MODEL: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    class Config:
        env_file = Path(__file__).parent.parent / ".env"

settings = Settings()