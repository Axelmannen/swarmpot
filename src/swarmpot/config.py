from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SWARMPOT_", extra="ignore")

    proxy_timeout_seconds: float = 30.0
    proxy_max_response_bytes: int = 10_000_000
    # Lets the proxy reach localhost and private networks. Local dev only: in production it is an SSRF hole.
    proxy_allow_private_targets: bool = False
    # SQLite file for the public record of settled payments.
    ledger_path: str = "swarmpot.sqlite3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
