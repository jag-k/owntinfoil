import asyncio
import html
import sys
import urllib.parse
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Self

from aiofile import async_open
from aiohttp import ClientError, ClientSession, ClientTimeout, encode_basic_auth

from app.config import settings


def gen_session() -> ClientSession:
    return ClientSession(
        headers={"Authorization": encode_basic_auth("user", settings.bot_key.get_secret_value())},
        timeout=ClientTimeout(total=30),
    )


class BaseClient:
    def __init__(self, print_errors: bool = True):
        self._session = gen_session()
        self._open_count = 0
        self._print_errors = print_errors

    async def __aenter__(self) -> ClientSession:
        self._open_count += 1
        if self._open_count == 1:
            await self._session.__aenter__()
        return self._session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._open_count -= 1
        if self._open_count == 0:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def _get(self, url: str) -> str | None:
        async with self as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.text()
            except (TimeoutError, ClientError, UnicodeError) as error:
                if self._print_errors:
                    # Exception text and URLs can contain the bot key.
                    status = getattr(error, "status", None)
                    print(f"Bot catalog request failed: {type(error).__name__}, HTTP status={status}", file=sys.stderr)
                return None


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, "".join(self._text)))
            self._href = None


@dataclass
class URL:
    data_url: str
    name: str

    @classmethod
    def parse_a(cls, string: str) -> Self | None:
        parser = LinkParser()
        parser.feed(string)
        return cls(*parser.links[0]) if parser.links else None

    def __post_init__(self):
        self.name = self.normalize_name(self.name)

    async def get_data(self, retries: int = 2) -> bytes:
        async with gen_session() as session:
            for attempt in range(retries):
                try:
                    async with session.get(self.abs_url) as response:
                        response.raise_for_status()
                        return await response.read()
                except (TimeoutError, ClientError) as error:
                    print(f"Torrent request failed: {type(error).__name__}", file=sys.stderr)
                    if attempt + 1 < retries:
                        await asyncio.sleep(0.5)
        return b""

    @staticmethod
    def normalize_name(name: str) -> str:
        return html.unescape(urllib.parse.unquote(name)).split("_&&_")[-1]

    @property
    def abs_url(self) -> str:
        return urllib.parse.urljoin(settings.bot_url.rstrip("/") + "/", self.data_url)

    async def save_torrent(self) -> Path | None:
        # A remote filename must never escape the watched torrent directory.
        if not self.name or self.name in {".", ".."} or "/" in self.name or "\\" in self.name:
            print("Skipping unsafe torrent filename", file=sys.stderr)
            return None
        path = settings.torrent_dir / self.name
        data = await self.get_data()
        if not data:
            return None
        # Transmission must see a completed file, not an in-progress write.
        temporary = path.with_name(path.name + ".part")
        try:
            async with async_open(temporary, "wb") as file:
                await file.write(data)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
        return path

    def __str__(self) -> str:
        return self.name


class Client(BaseClient):
    def __init__(self, print_errors: bool = True):
        super().__init__(print_errors=print_errors)
        self._saved: set[str] = set()

    async def _get_data(self) -> str | None:
        return await self._get(settings.bot_url)

    async def parse_data(self):
        data = await self._get_data()
        if data is None:
            return {"torrents": [], "update": None}
        parser = LinkParser()
        parser.feed(data or "")
        torrents = []
        for href, name in parser.links:
            url = URL(href, name)
            remote = urllib.parse.urlsplit(url.abs_url)
            base = urllib.parse.urlsplit(settings.bot_url)
            filename = urllib.parse.unquote(remote.path.rsplit("/", 1)[-1])
            if (
                (remote.scheme, remote.netloc) == (base.scheme, base.netloc)
                and settings.bot_key.get_secret_value()
                and filename.startswith(f"{settings.bot_key.get_secret_value()}_")
                and filename.lower().endswith(".torrent")
            ):
                torrents.append(url)
        self._saved.intersection_update(url.abs_url for url in torrents)
        return {"torrents": [url for url in torrents if url.abs_url not in self._saved], "update": None}

    async def parse_and_save(self, print_urls: bool = False):
        data = await self.parse_data()
        if print_urls and data["torrents"]:
            print(f"Found {len(data['torrents'])} torrent(s)!", file=sys.stderr)
        paths = []
        for torrent in data["torrents"]:
            try:
                path = await torrent.save_torrent()
            except OSError as error:
                print(f"Cannot save torrent: {type(error).__name__}", file=sys.stderr)
                path = None
            if path is not None:
                self._saved.add(torrent.abs_url)
            paths.append(path)
        return paths


async def loop():
    client = Client()
    async with client:
        try:
            print("Loop started!", file=sys.stderr)
            print("Press Ctrl+C to exit", file=sys.stderr)
            while True:
                await client.parse_and_save(True)
                await asyncio.sleep(5)
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
