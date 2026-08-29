import os

# Sync Streamlit secrets into os.environ if available (e.g. for Streamlit Community Cloud)
try:
    import streamlit as st
    if hasattr(st, "secrets"):
        for k, v in st.secrets.items():
            if isinstance(v, str) and k not in os.environ:
                os.environ[k] = v
except Exception:
    pass

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_LLM_MODEL: str = "nvidia/nemotron-3.5-lightning:free"
    OPENROUTER_EMBEDDING_MODEL: str = "liquid/lfm2.5-embedding-350m"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"
    
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.30
    
    MAX_FILE_SIZE_MB: int = 10
    
    OCR_ENABLED: bool = True
    OCR_LANGUAGE: str = "eng"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

