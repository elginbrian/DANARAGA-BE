import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):

    PROJECT_NAME: str = "Danaraga API"
    API_V1_STR: str = "/api"

    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "danaraga_db_dev")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your_default_super_secret_key")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MIDTRANS_SERVER_KEY: str = os.getenv("MIDTRANS_SERVER_KEY", "")
    MIDTRANS_CLIENT_KEY: str = os.getenv("MIDTRANS_CLIENT_KEY", "")
    MIDTRANS_IS_PRODUCTION: bool = False

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()