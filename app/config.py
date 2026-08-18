from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Clic KiuSys PSS API"
    environment: str = "pruebas"
    database_url: str = "postgresql://pss:pss@localhost:5432/pss_pruebas"
    hold_minutes: int = 10


settings = Settings()
