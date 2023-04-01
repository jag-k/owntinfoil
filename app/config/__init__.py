# flake8: noqa: F403

import os

from dotenv import load_dotenv

from app.config.base import *

try:
    from app.config.local import *

except ImportError:
    pass

load_dotenv()

for key in dir():
    if key.isupper():
        locals()[key] = os.getenv(key, locals()[key])

if not isinstance(NPS_DIR, Path):
    NPS_DIR = Path(NPS_DIR)

if not isinstance(TORRENT_DIR, Path):
    TORRENT_DIR = Path(TORRENT_DIR)

NPS_DIR.mkdir(parents=True, exist_ok=True)
TORRENT_DIR.mkdir(parents=True, exist_ok=True)
