from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GROQ_API_KEY: str
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_API_KEY: str
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    AVIATIONSTACK_STACK_API_KEY: str
    TAVILY_API_KEY: str
    OPENWEATHERMAP_API_KEY: str
    DATABASE_URL: str
    GMAIL_EMAIL: str
    GMAIL_SMTP_PASSWORD: str
    SECRET_KEY: str
    APP_URL: str = "http://localhost:8000"

    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7


settings = Settings()
