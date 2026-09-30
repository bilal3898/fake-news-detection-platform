# ml_core/settings.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "bilal@3132"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "fake_news_db"
    MODEL_PATH: str = "ml_core/models/model_20250917_000744"

    @property
    def DATABASE_URL(self):
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

settings = Settings()

def get_settings():
    return settings
