from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent.parent.parent
NPS_DIR = BASE_PATH / "NPSdir"
TORRENT_DIR = BASE_PATH / "TORRENTdir"

BOT_KEY: str | None = None
BOT_URL: str = "http://example.com/"
OVERRIDE_TORRENTS: bool = True
SUCCESS_MESSAGE: str = (
    "Please join telegram bot @Switch_library_bot (password 'marsel') - get games at maximum speed, "
    "before tinfoil shops and absolutely free!"
)

HOST: str = "0.0.0.0"  # noqa: S104
PORT: int = 8080

__all__ = (
    "BASE_PATH",
    "NPS_DIR",
    "TORRENT_DIR",
    "BOT_KEY",
    "BOT_URL",
    "OVERRIDE_TORRENTS",
    "SUCCESS_MESSAGE",
    "HOST",
    "PORT",
)
