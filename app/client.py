import asyncio
import html
import re
import sys
import urllib.parse
from dataclasses import dataclass
from typing import Self

import config
from aiofile import async_open
from aiohttp import BasicAuth, ClientSession, ServerDisconnectedError


def gen_session():
    return ClientSession(auth=BasicAuth("user", config.BOT_KEY))


class BaseClient:
    def __init__(self):
        self.__post_init__()

    def __post_init__(self):
        self._session = gen_session()
        self._open_count = 0
        self._open_result = None

    async def __aenter__(self):
        self._open_count += 1
        if self._open_count == 1:
            self._open_result = await self._session.__aenter__()
        return self._open_result

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._open_count -= 1
        if self._open_count == 0:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def _get(self, url: str) -> str | None:
        async with self as session:
            try:
                async with session.get(url) as response:
                    return await response.text()
            except ServerDisconnectedError:
                print(f"Server disconnected for url {url!r}!", file=sys.stderr)
                return None


@dataclass
class URL:
    data_url: str
    name: str

    @classmethod
    def parse_a(cls, string: str) -> Self | None:
        m = re.compile(r'<a href="(?P<data_url>.+?)">(?P<name>.+?)</a>').match(string)
        if m:
            return cls(**m.groupdict())
        return None

    def __post_init__(self):
        self.name = self.normalize_name(self.name)

    async def get_data(self, retries: int = 2) -> bytes:
        original_retries = retries
        async with gen_session() as session:
            while retries:
                try:
                    async with session.get(self.abs_url) as response:
                        return await response.content.read()
                except ServerDisconnectedError:
                    print(f"Server disconnected for file {self.name!r}, retrying...", file=sys.stderr)
                    retries -= 1
            print(f"Failed to download file {self.name!r} after {original_retries} retries!", file=sys.stderr)

    @staticmethod
    def normalize_name(name: str) -> str:
        return html.unescape(urllib.parse.unquote(name)).split("_&&_")[-1]

    @property
    def abs_url(self):
        return f"{config.BOT_URL.rstrip('/')}/{self.data_url}"

    async def save_torrent(self):
        path = config.TORRENT_DIR / self.name
        data = await self.get_data()
        if not data:
            print(f"Failed to download torrent {self.name!r}! Skipping...", file=sys.stderr)
            return
        async with async_open(path, "wb") as file:
            await file.write(data)
        return path

    def __str__(self):
        return f"{self.name} ({self.abs_url})"


class Client(BaseClient):
    def __init__(self):
        super().__init__()
        self._temp_cache = None

    async def _get_data(self) -> str | None:
        return await self._get(config.BOT_URL)

    async def parse_data(self):
        default_dict = {"torrents": [], "update": None}
        data = await self._get_data()
        if not data:
            return default_dict
        ul = data.split("<ul>", 1)[-1].split("</ul>", 1)[0]
        result: list[URL] = [URL.parse_a(li.split("</li>", 1)[0]) for li in ul.split("<li>")[1:]]
        ret = {
            "torrents": [url for url in result[:-1] if url.data_url.startswith(f"{config.BOT_KEY}_")],
            "update": result[-1],
        }
        if self._temp_cache is None:
            self._temp_cache = ret
            return ret
        if self._temp_cache["torrents"] != ret["torrents"]:
            self._temp_cache = ret
            return ret
        return default_dict

    async def parse_and_save(self, print_urls: bool = False):
        data = await self.parse_data()
        if print_urls and data["torrents"]:
            print(f"Found {len(data['torrents'])} torrent(s)!", *data["torrents"], sep="\n\t", file=sys.stderr)
        return await asyncio.gather(*(torrent.save_torrent() for torrent in data["torrents"]))


async def loop():
    client = Client()
    async with client:
        try:
            print("Loop started!", file=sys.stderr)
            print("Press Ctrl+C to exit", file=sys.stderr)
            while True:
                await client.parse_and_save(True)
        except KeyboardInterrupt:
            print("Exiting...", file=sys.stderr)


async def main():
    client = Client()
    async with client:
        data = await client.parse_data()
        print(len(data["torrents"]), *data["torrents"], sep="\n", file=sys.stderr)
        for torrent in data["torrents"]:
            print(await torrent.save_torrent(), file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(loop())
