from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from typing import Literal

# BaseSetting Automatically reads configurations value from environment variables / .env

class Settings(BaseSettings):
    # DATABASE_URL:str
    REDIS_URL: str
    CACHE_KEY_SECRET: str
    JWT_SECRET_KEY:str
    JWT_ALGORITHM:str="HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES:int=30
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    GROQ_MODEL:str
    GEMINI_EVAL_MODEL:str
    GROQ_API_KEY:str
    GOOGLE_API_KEY:str
    GROQ_FAST_MODEL:str
    DATABASE_URL: str
    LANGGRAPH_CHECKPOINTER_URL: str
    APP_ENV: Literal[
        "development",
        "testing",
        "production"
    ] = "production"


    # LangSmith Observability

    LANGSMITH_TRACING: bool = False

    LANGSMITH_ENDPOINT: str = (
        "https://api.smith.langchain.com"
    )

    LANGSMITH_API_KEY: SecretStr | None = None

    LANGSMITH_PROJECT: str = "HealthGuard-AI"



    AWS_S3_BUCKET: str
    MAX_FILE_SIZE_MB: int = 10
    model_config=SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    # AI Gateway Reliability

    AI_MODEL_TIMEOUT: int = 30
    # S3 encryption
    S3_SERVER_SIDE_ENCRYPTION: str = "AES256"

    AI_MODEL_MAX_RETRIES: int = 2

settings=Settings()
