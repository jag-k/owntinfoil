import asyncio
import json
import sys

from aiohttp import web
from aiohttp_basicauth import BasicAuthMiddleware

from app.client import Client
from app.config import settings
from app.generate_tfl import generate_tfl_file


class BasicAuth(BasicAuthMiddleware):
    async def check_credentials(self, username: str, password: str, request):  # ruff: ignore[no-self-use]
        expected = settings.http_auth_users.get(username)
        return expected is not None and password == expected.get_secret_value()


async def redirect(_: web.Request) -> web.Response:  # ruff: ignore[unused-async]
    raise web.HTTPFound("/shop.tfl")


async def handler(_: web.Request) -> web.Response:  # ruff: ignore[unused-async]
    data = json.dumps(generate_tfl_file())
    return web.Response(text=data, content_type="application/json", charset="utf-8")


async def periodic_request():
    if not settings.bot_url or not settings.bot_key.get_secret_value():
        print("Bot sync disabled: set both BOT_URL and BOT_KEY to enable it.", file=sys.stderr)
        return
    client = Client()
    async with client:
        while True:
            await client.parse_and_save(True)
            await asyncio.sleep(5)


async def prepare_server(host: str, port: int) -> tuple[web.TCPSite, web.AppRunner]:
    settings.ensure_directories()
    app = web.Application()
    app.add_routes(
        [
            web.get("/", redirect),
            web.get("/shop.tfl", handler),
            web.static("/", settings.nps_dir, follow_symlinks=True),
        ],
    )
    if settings.http_auth_users:
        app.middlewares.append(BasicAuth())
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    return site, runner


async def run_server(site: web.TCPSite):
    await site.start()
    await asyncio.Event().wait()


async def run():
    site, runner = await prepare_server(settings.host, settings.port)
    try:
        await asyncio.gather(run_server(site), periodic_request())
    finally:
        await site.stop()
        await runner.cleanup()


def main():
    # noinspection HttpUrlsUsage
    print(f"Server started at http://{settings.host}:{settings.port}", file=sys.stderr)
    print("Press CTRL+C to exit", file=sys.stderr)
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Exiting...", file=sys.stderr)


if __name__ == "__main__":
    main()
