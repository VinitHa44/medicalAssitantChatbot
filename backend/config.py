from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # API Keys
    LLAMA_API_KEY: str  # Groq API key for Llama 3
    LLAMA_MODEL: str = "llama-3.3-70b-versatile"  # Default Llama 3 model
    
    # Pinecone Configuration
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str = "medical-chatbot"
    
    # MongoDB Configuration
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "medical_chatbot"
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    CACHE_TTL: int = 3600
    
    # Application Settings
    APP_NAME: str = "Medical Assistant Chatbot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Voice Settings
    WHISPER_MODEL: str = "base"
    TTS_MODEL: str = "tts_models/en/ljspeech/tacotron2-DDC"
    
    # RAG Settings
    CHUNK_SIZE: int = 2000
    CHUNK_OVERLAP: int = 200
    TOP_K_RESULTS: int = 5
    CONFIDENCE_THRESHOLD: float = 0.6
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    class Config:
        # Look for .env file in project root (parent directory)
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields (like VITE_* frontend vars)


settings = Settings()
