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
    # Default to 'gemini' when a key is present, 'mock' as safe offline fallback
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_PROVIDER: str = os.getenv(
        "LLM_PROVIDER",
        "gemini" if os.getenv("GEMINI_API_KEY", "") else "mock"
    )  # auto-selects 'gemini' when key available, else 'mock'

    # Weather API keys (both common names accepted)
    OPENWEATHER_API_KEY: str = (
        os.getenv("OPENWEATHER_API_KEY") or
        os.getenv("OPENWEATHERMAP_API_KEY") or
        os.getenv("OWM_API_KEY") or ""
    )
    WEATHERAPI_API_KEY: str = os.getenv("WEATHERAPI_API_KEY", "")

    # Geocode LRU cache TTL (seconds)
    GEOCODE_CACHE_TTL: int = int(os.getenv("GEOCODE_CACHE_TTL", "600"))  # 10 minutes
    
    # Graph City Parameters
    GRID_SIZE: int = 10  # 10x10 city grid of intersections
    DEFAULT_CAPACITY: float = 100.0  # vehicle capacity per road segment

settings = Settings()
