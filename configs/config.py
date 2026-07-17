import os
from dotenv import load_dotenv

# Load root .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

class Settings:
    PROJECT_NAME: str = "MIRROR CITY"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-key-for-mirror-city-12345")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # DB
    DATABASE_PATH: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "mirror_city.db")
    )
    DATABASE_URL: str = f"sqlite:///{DATABASE_PATH}"
    
    # LLM Settings (supports provider switching)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")  # 'gemini', 'openai', or 'mock'
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Graph City Parameters
    GRID_SIZE: int = 10  # 10x10 city grid of intersections
    DEFAULT_CAPACITY: float = 100.0  # vehicle capacity per road segment

settings = Settings()
