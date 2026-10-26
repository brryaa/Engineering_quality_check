import os
from pydantic import BaseModel

DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "eql_platform.db"))


class Settings(BaseModel):
    PROJECT_NAME: str = "汽车研发工程质量管理平台 (Engineering Quality Lab)"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # SQLite configuration with WAL mode (defaults to backend directory)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

    # Security & Rate Limiting (High default allows extensive automated test suites and high-cadence UI interactions)
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "10000"))
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    MAX_BODY_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB

    # Authentication & JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "eql-automotive-engineering-secret-key-change-in-production-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8088",
        "http://127.0.0.1:8088",
    ]


settings = Settings()
