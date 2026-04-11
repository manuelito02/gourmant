from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://gourmant:gourmant@localhost:5432/gourmant"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
