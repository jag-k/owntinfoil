import asyncio
import tempfile
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import patch

from aiohttp import ClientSession, ClientTimeout, encode_basic_auth, web
from pydantic import SecretStr

from app.client import URL, Client
from app.config import settings
from app.generate_tfl import generate_tfl_file
from app.main import prepare_server


def respond(*, text: str | None = None, body: bytes | None = None, status: int = 200):
    async def handler(_: web.Request):
        return web.Response(text=text, body=body, status=status)

    return handler


def site_url(runner: web.AppRunner) -> str:
    return f"http://127.0.0.1:{runner.addresses[0][1]}"


class ServerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patches = [
            patch.object(settings, "torrent_dir", self.root),
            patch.object(settings, "bot_key", SecretStr("test-key")),
        ]
        for item in self.patches:
            item.start()
        self.runners = []

    async def asyncTearDown(self):
        for runner in self.runners:
            await runner.cleanup()
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    async def serve(self, app):
        runner = web.AppRunner(app)
        await runner.setup()
        self.runners.append(runner)
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        return site_url(runner)

    async def test_local_shop_and_range_download(self):
        (self.root / "demo.nsp").write_bytes(b"0123456789")
        with (
            patch.object(settings, "nps_dir", self.root),
            patch("app.main.generate_tfl_file", partial(generate_tfl_file, self.root)),
        ):
            site, runner = await prepare_server("127.0.0.1", 0)
            self.runners.append(runner)
            await site.start()
            base = site_url(runner)
            async with ClientSession() as session:
                async with session.get(base) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual((await response.json())["files"][0]["size"], 10)
                async with session.get(base + "/demo.nsp", headers={"Range": "bytes=2-5"}) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(await response.read(), b"2345")

    async def test_shop_escapes_special_characters_in_filenames(self):
        (self.root / "demo #1.nsp").write_bytes(b"fixture")
        data = generate_tfl_file(self.root)
        self.assertEqual(data["files"][0]["url"], "../demo%20%231.nsp")

    async def test_local_http_auth(self):
        with (
            patch.object(settings, "nps_dir", self.root),
            patch.object(settings, "http_auth_users", {"tester": SecretStr("password")}),
        ):
            site, runner = await prepare_server("127.0.0.1", 0)
            self.runners.append(runner)
            await site.start()
            base = site_url(runner)
            async with ClientSession() as session:
                async with session.get(base + "/shop.tfl") as response:
                    self.assertEqual(response.status, 401)
                async with session.get(
                    base + "/shop.tfl", headers={"Authorization": encode_basic_auth("tester", "password")}
                ) as response:
                    self.assertEqual(response.status, 200)

    async def test_bot_auth_and_single_link_without_update_marker(self):
        async def catalog(request):
            self.assertEqual(request.headers["Authorization"], encode_basic_auth("user", "test-key"))
            return web.Response(
                text="<ul><li><a href='test-key_&amp;&amp;_demo.torrent'><b>demo.torrent</b></a></li></ul>"
            )

        app = web.Application()
        app.router.add_get("/", catalog)
        app.router.add_get("/test-key_&&_demo.torrent", respond(body=b"test fixture"))
        base = await self.serve(app)
        with patch.object(settings, "bot_url", base):
            client = Client()
            async with client:
                paths = await client.parse_and_save()
                self.assertEqual(paths, [self.root / "demo.torrent"])
                self.assertEqual(paths[0].read_bytes(), b"test fixture")
                self.assertEqual(await client.parse_and_save(), [])
                self.assertFalse(list(self.root.glob("*.part")))

    async def test_bad_responses_are_nonfatal(self):
        for status, body in [(401, "Unauthorized"), (503, "Unavailable"), (200, "<html>no links</html>")]:
            app = web.Application()
            app.router.add_get("/", respond(status=status, text=body))
            base = await self.serve(app)
            with patch.object(settings, "bot_url", base):
                client = Client(print_errors=False)
                async with client:
                    self.assertEqual(await client.parse_and_save(), [])

    async def test_failed_download_retried_next_poll(self):
        attempts = 0

        async def download(_):
            nonlocal attempts
            attempts += 1
            return web.Response(status=503 if attempts <= 2 else 200, body=b"fixture")

        app = web.Application()
        app.router.add_get("/", respond(text='<a href="test-key_demo.torrent">demo.torrent</a>'))
        app.router.add_get("/test-key_demo.torrent", download)
        base = await self.serve(app)
        with patch.object(settings, "bot_url", base):
            client = Client()
            async with client:
                self.assertEqual(await client.parse_and_save(), [None])
                self.assertEqual(await client.parse_and_save(), [self.root / "demo.torrent"])

    async def test_timeout_is_nonfatal(self):
        async def slow(_):
            await asyncio.sleep(0.05)
            return web.Response(text="")

        app = web.Application()
        app.router.add_get("/", slow)
        base = await self.serve(app)
        with patch.object(settings, "bot_url", base):
            client = Client(print_errors=False)
            client._session._timeout = ClientTimeout(total=0.01)
            async with client:
                self.assertEqual(await client.parse_and_save(), [])

    async def test_invalid_url_is_nonfatal(self):
        with patch.object(settings, "bot_url", ""):
            client = Client(print_errors=False)
            async with client:
                self.assertEqual(await client.parse_and_save(), [])

    async def test_external_links_are_ignored(self):
        app = web.Application()
        app.router.add_get("/", respond(text='<a href="http://other.invalid/test-key_demo.torrent">demo.torrent</a>'))
        base = await self.serve(app)
        with patch.object(settings, "bot_url", base):
            client = Client()
            async with client:
                self.assertEqual((await client.parse_data())["torrents"], [])

    async def test_unsafe_filename_is_ignored(self):
        self.assertIsNone(await URL("anything", "../escape.torrent").save_torrent())


if __name__ == "__main__":
    unittest.main()
