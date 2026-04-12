import secrets

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://gourmant:gourmant@localhost:5432/gourmant"
    redis_url: str = "redis://localhost:6379/0"
    # Random default keeps dev working out of the box; sessions reset on restart.
    # Set SECRET_KEY in .env (or environment) for a stable key in production.
    secret_key: str = secrets.token_hex(32)

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
