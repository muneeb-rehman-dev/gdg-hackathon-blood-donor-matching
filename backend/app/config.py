from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    database_url: str = "sqlite+aiosqlite:///./blood_donor.db"
    cors_origins: str = "http://localhost:3000"
    wave_size: int = 10
    min_donors_per_request: int = 3

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
