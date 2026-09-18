from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "agro-asistente"
    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "agro_asistente"

    jwt_secret: str = "change-me-in-local-env-do-not-use-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 120

    knowledge_dir: str = "../knowledge"

    chroma_persist_dir: str = "./chroma_data"
    chroma_collection: str = "agro_knowledge_pmv1"

    rag_top_k: int = 3
    rag_min_similarity: float = 0.12
    chunk_size: int = 500

    embedding_provider: str = "local"
    embedding_dimension: int = 128
    embedding_api_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""

    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def mysql_url(self) -> str:
        if self.mysql_password:
            auth = f"{self.mysql_user}:{self.mysql_password}"
        else:
            auth = self.mysql_user
        return (
            f"mysql+pymysql://{auth}@{self.mysql_host}:{self.mysql_port}/"
            f"{self.mysql_database}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
