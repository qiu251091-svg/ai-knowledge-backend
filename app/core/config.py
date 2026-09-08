from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI Knowledge Backend"
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"
    model_config = {"env_file": ".env"}

settings = Settings()
