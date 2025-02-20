from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://negowars_user:negowars_password@localhost/negowars_db"
    secret_key: str = "6fe483598186c90c41f605ca5c9b27e4450a222b171ccf156a815d03bf23aa7c"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours (for development ONLY)
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

settings = Settings() 