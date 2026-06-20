import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str = "ai-fitness-arena-backend"
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/ai_fitness_arena",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-me")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))


settings = Settings()
