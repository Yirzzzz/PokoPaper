from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[4] / ".env"
API_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    api_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    postgres_url: str = "postgresql://postgres:postgres@localhost:5432/pokomon"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    storage_dir: str = "./storage"
    use_mock_services: bool = True
    database_echo: bool = False
    modelscope_base_url: str = "https://api-inference.modelscope.cn/v1"
    modelscope_api_key: str = ""
    modelscope_model: str = "ZhipuAI/GLM-4.7-Flash"
    modelscope_enable_thinking: bool = False
    modelscope_thinking_budget: int | None = None
    dashscope_base_url: str = ""
    dashscope_api_key: str = ""
    dashscope_model: str = "ZhipuAI/GLM-4.7"
    dashscope_enable_thinking: bool = False
    dashscope_thinking_budget: int | None = None

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV), str(API_ENV), ".env"),
        extra="ignore",
    )


settings = Settings()
