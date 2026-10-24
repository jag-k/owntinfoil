from pathlib import Path
from typing import Any, override

from pydantic import Field, SecretStr, field_validator
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, EnvSettingsSource, PydanticBaseSettingsSource, SettingsConfigDict

BASE_PATH = Path(__file__).resolve().parent.parent


class LegacyAuthSource(PydanticBaseSettingsSource):
    def __init__(self, settings_cls: type[BaseSettings], sources: tuple[PydanticBaseSettingsSource, ...]):
        super().__init__(settings_cls)
        self.sources = sources

    @override
    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        # Keep HTTP_AUTH_USER_1=username:password working in both .env and Docker.
        users = {}
        for source in self.sources:
            if isinstance(source, EnvSettingsSource):
                for key, value in source.env_vars.items():
                    if key.startswith("http_auth_user_") and value and ":" in value:
                        username, password = value.split(":", 1)
                        users[username] = password
        return {"http_auth_users": users}


class Settings(BaseSettings):
    """OwnTinfoil HTTP shop and optional bot synchronization settings.

    Environment variables override the project .env file. Bot synchronization
    requires both BOT_URL and BOT_KEY; the local shop works without them.
    """

    model_config = SettingsConfigDict(
        env_file=BASE_PATH / ".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
        str_strip_whitespace=True,
        hide_input_in_errors=True,
    )

    nps_dir: Path = Field(
        default=BASE_PATH / "NPSdir",
        description=(
            "Directory containing files served by the HTTP shop, including subdirectories. "
            "Created on server startup. Docker uses /nps; the NPSdir spelling is retained for compatibility."
        ),
        examples=["./NPSdir", "/nps"],
    )
    torrent_dir: Path = Field(
        default=BASE_PATH / "TORRENTdir",
        description=(
            "Directory where bot torrent files are saved for the torrent client's watch folder. "
            "Created on server startup. Docker shares /torrents with Transmission's /watch."
        ),
        examples=["./TORRENTdir", "/torrents"],
    )
    bot_key: SecretStr = Field(
        default=SecretStr(""),
        description=(
            "Bot synchronization key used as the HTTP Basic Auth password for username user. "
            "Leave empty to disable synchronization. Leading and trailing whitespace is removed."
        ),
        examples=["replace-with-your-bot-key"],
    )
    bot_url: str = Field(
        default="",
        description=(
            "Base HTTP or HTTPS URL of the bot's torrent directory, including its port if needed. "
            "Set together with BOT_KEY to enable synchronization. Leave empty for a standalone local shop."
        ),
        examples=["http://bot.example.com:8878/"],
    )
    host: str = Field(
        default="0.0.0.0",  # ruff: ignore[hardcoded-bind-all-interfaces]
        description=(
            "Address on which the HTTP server listens. Use 0.0.0.0 for LAN or Docker access, "
            "or 127.0.0.1 for this computer only. In Tinfoil, enter the server's reachable LAN address."
        ),
        examples=["0.0.0.0", "127.0.0.1"],  # ruff: ignore[hardcoded-bind-all-interfaces]
    )
    port: int = Field(
        default=8080,
        ge=1,
        le=65535,
        description=(
            "HTTP server listening port, from 1 to 65535. Docker publishes container port 8080; "
            "keep this value at 8080 unless you also change the container port mapping."
        ),
        examples=[8080, 8090],
    )
    http_auth_users: dict[str, SecretStr] = Field(
        default_factory=dict,
        description=(
            "Local shop HTTP Basic Auth users as a JSON object mapping usernames to passwords. "
            "An empty object disables authentication. HTTP_AUTH_USERS__username=password is also supported, "
            "as is the legacy HTTP_AUTH_USER_1=username:password format. These are separate from BOT_KEY."
        ),
        examples=['{"player":"replace-with-a-password"}'],
    )
    success_message: str = Field(
        default=(
            "Please join telegram bot @Switch_library_bot (password 'marsel') - get games at maximum speed, "
            "before tinfoil shops and absolutely free!"
        ),
        description="Message included in the shop.tfl JSON response and displayed by Tinfoil.",
        examples=["Welcome to my local library."],
    )

    @field_validator("bot_key", mode="before")
    @classmethod
    def strip_bot_key(cls, value: str | SecretStr) -> str | SecretStr:
        return value.strip() if isinstance(value, str) else value

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        legacy_auth = LegacyAuthSource(settings_cls, (dotenv_settings, env_settings))
        return init_settings, env_settings, dotenv_settings, legacy_auth, file_secret_settings

    def ensure_directories(self) -> None:
        self.nps_dir.mkdir(parents=True, exist_ok=True)
        self.torrent_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
