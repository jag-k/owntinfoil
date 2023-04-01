import asyncio
import json
import sys
import warnings
from asyncio import AbstractEventLoop

from aiohttp import web
from config import HOST, PORT

from app.client import Client
from app.generate_tfl import generate_tfl_file


async def redirect(_):
    return web.HTTPFound("/shop.tfl")


async def handler(_):
    data = json.dumps(generate_tfl_file())
    return web.Response(text=data, content_type="application/json", charset="utf-8")


async def periodic_request():
    client = Client()
    async with client:
        while True:
            await client.parse_and_save(True)
            await asyncio.sleep(0.5)


async def run(loop: AbstractEventLoop, host: str, port: int):
    app = web.Application()
    app.add_routes([web.get("/", redirect), web.get("/shop.tfl", handler)])
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    server = await loop.create_server(app.make_handler(), host, port)
    await asyncio.gather(server.serve_forever(), periodic_request())


def main():
    loop = asyncio.get_event_loop()
    print(f"Server started at http://{HOST}:{PORT}", file=sys.stderr)
    print("Press CTRL+C to exit", file=sys.stderr)
    try:
        loop.run_until_complete(run(loop, HOST, PORT))
    except KeyboardInterrupt:
        print("Exiting...", file=sys.stderr)


if __name__ == "__main__":
    main()
