import os
from functools import cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WireConfig(BaseSettings):
    app_name: str = "wire"
    admin_email: str = ""

    port: int = 1818
    log_level: str = "info"

    # db
    # db_url: str
    # db_autocommit: bool

    # redis
    # valkey_endpoint: str
    # valkey_port: int = 6379
    # valkey_db: int = 0

    # bulb
    bulb_base_url: str

    # misc
    sentry_dsn: str

    # load config
    model_config = SettingsConfigDict(env_file=os.getenv("WIRE_CONFIG_PATH", "wire.env"))


@cache
def load_wire_cfg() -> WireConfig:
    return WireConfig.model_validate({})
