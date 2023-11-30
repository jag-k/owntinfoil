import contextlib
import os
from pathlib import Path

from dotenv import load_dotenv

from app.config.base import *

with contextlib.suppress(ImportError):
    from app.config.local import *

load_dotenv()

for key in dir():
    if key.isupper():
        locals()[key] = os.getenv(key, locals()[key])

if not isinstance(NPS_DIR, Path):
    NPS_DIR = Path(NPS_DIR)

if not isinstance(TORRENT_DIR, Path):
    TORRENT_DIR = Path(TORRENT_DIR)

# noinspection PyUnboundLocalVariable
NPS_DIR.mkdir(parents=True, exist_ok=True)
# noinspection PyUnboundLocalVariable
TORRENT_DIR.mkdir(parents=True, exist_ok=True)

HTTP_AUTH_USERS = {}
for key, user_and_password in os.environ.items():
    if not key.startswith("HTTP_AUTH_USER_"):
        continue
    try:
        user, password = user_and_password.split(":", 1)
        HTTP_AUTH_USERS[user] = password
    except ValueError:
        continue

if BOT_KEY is None:
    raise ValueError("BOT_KEY must be set!")
