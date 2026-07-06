from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Mocks: True = sin cuentas externas
    cf_mock: bool = True
    auth_mock: bool = True

    # Cloudflare Stream
    cf_account_id: str = ""
    cf_stream_api_token: str = ""

    # Clerk
    clerk_secret_key: str = ""
    clerk_jwks_url: str = ""
    clerk_issuer: str = ""

    # App
    db_path: str = "data/app.db"
    uploads_dir: str = "data/uploads"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
