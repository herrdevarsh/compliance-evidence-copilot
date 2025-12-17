from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_url: str
    embed_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k: int = 6
    min_dense_score: float = 0.25

    openai_api_key: str | None = None
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    mlflow_tracking_uri: str | None = None

settings = Settings()
