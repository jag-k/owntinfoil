import asyncio
import json
import sys
import warnings

from aiohttp import web
from aiohttp_basicauth import BasicAuthMiddleware

from app.client import Client
from app.config import HOST, HTTP_AUTH_USERS, NPS_DIR, PORT
from app.generate_tfl import generate_tfl_file


class BasicAuth(BasicAuthMiddleware):
    async def check_credentials(self, username: str, password: str, request):  # noqa: PLR6301
        return password == HTTP_AUTH_USERS.get(username)


async def redirect(_: web.Request) -> web.Response:
    return web.HTTPFound("/shop.tfl")


async def handler(_: web.Request) -> web.Response:
    data = json.dumps(generate_tfl_file())
    return web.Response(text=data, content_type="application/json", charset="utf-8")


async def periodic_request():
    client = Client()
    async with client:
        while True:
            await client.parse_and_save(True)
            await asyncio.sleep(0.5)


async def prepare_server(host: str, port: int) -> tuple[web.TCPSite, web.AppRunner]:
    app = web.Application()
    app.add_routes(
        [
            web.get("/", redirect),
            web.get("/shop.tfl", handler),
            web.static("/", NPS_DIR, follow_symlinks=True),
        ],
    )
    if HTTP_AUTH_USERS:
        app.middlewares.append(BasicAuth())
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    return site, runner


async def run_server(site: web.TCPSite):
    await site.start()
    while True:
        await asyncio.sleep(3600)


async def run():
    site, runner = await prepare_server(HOST, PORT)
    try:
        await asyncio.gather(run_server(site), periodic_request())
    finally:
        await site.stop()
        await runner.cleanup()


def main():
    loop = asyncio.get_event_loop()
    # noinspection HttpUrlsUsage
    print(f"Server started at http://{HOST}:{PORT}", file=sys.stderr)
    print("Press CTRL+C to exit", file=sys.stderr)
    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Exiting...", file=sys.stderr)


if __name__ == "__main__":
    main()
