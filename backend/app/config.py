from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "StudyFlow PDF AI"
    app_env: str = "development"

    # Local: sqlite:///./studyflow.db
    # Railway + Supabase: postgresql://postgres:senha@host:5432/postgres
    database_url: str = "sqlite:///./studyflow.db"

    jwt_secret: str = "change_me_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    llm_provider: str = "mock"  # mock | gemini | openai | groq
    openai_api_key: str = ""
    gemini_api_key: str = ""
    groq_api_key: str = ""

    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_storage_bucket: str = "studyflow-documents"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
