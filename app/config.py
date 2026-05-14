from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://gourmant:gourmant@localhost:5432/gourmant"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str
    admin_email: str
    admin_password: str
    # Set to true in .env when running behind the Cloudflare Tunnel (HTTPS).
    # Keep false for local HTTP dev.
    session_cookie_secure: bool = False

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
