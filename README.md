# OwnTinfoil in Docker

[![GitHub Container Registry Build](https://img.shields.io/github/actions/workflow/status/jag-k/owntinfoil/deploy.yml?logo=github&label=Container%20Registry
)](https://github.com/users/jag-k/packages/container/package/owntinfoil)


Port on Python of the OwnTinfoil project.

More info you can find in [project's Wiki](https://github.com/jag-k/owntinfoil/wiki)

## Usage

### Requirements:

* [Docker](https://www.docker.com/)
* [Docker Compose](https://docs.docker.com/compose/) 2.24 or newer

### Install:

1. Copy the [docker-compose.yml](docker-compose.yml) file in your own directory
2. Optionally copy [.env.example](.env.example) to `.env` beside the Compose file and uncomment settings you need. Bot synchronization requires both `BOT_URL` and `BOT_KEY`; the local shop works without them.
3. Run `docker compose up -d`
4. Enjoy!

Connect Tinfoil using HTTP, your Docker host's LAN address, port `8080`, and path `/shop.tfl`. Do not use `0.0.0.0` as the client address. Put your local files in `NPSdir` (the folder name used by this port).

The bot endpoint requires a valid key. HTTP `401` means authentication was rejected; the local shop continues serving files when bot requests fail.

## How to ...

You can read the [Wiki page](https://github.com/jag-k/owntinfoil/wiki/How-to) for more information.

Also, you can read the [FAQ page](https://github.com/jag-k/owntinfoil/wiki/FAQ) for more information.

## Development

### Requirements:

* [Python 3.12](https://www.python.org/)
* [uv](https://docs.astral.sh/uv/)
* [Docker](https://www.docker.com/) (optional)

### How to install

1. Clone the repository
2. Run `uv sync --locked`
3. Enjoy!

### How to run

1. Optionally set both `BOT_URL` and `BOT_KEY` in `.env` to enable bot synchronization.
2. Run `uv run --locked python -m app`
3. Enjoy!

### Settings

See the generated [configuration reference](docs/configuration.md) for every setting, its default, description, and examples. The generated [.env.example](.env.example) is a starting point for your `.env` file. Uncomment only the values you want to override.

Environment variables override the project's `.env`. Both `BOT_URL` and `BOT_KEY` are needed for bot synchronization; the local shop works without them. For example:

```dotenv
BOT_URL=http://bot.example.com:8878/
BOT_KEY=replace-with-your-bot-key
HTTP_AUTH_USERS='{"player":"replace-with-a-password"}'
```

`HTTP_AUTH_USERS` protects your local shop; `BOT_KEY` authenticates to the remote bot. The legacy `HTTP_AUTH_USER_1=player:password` format is also supported.

### Build from source

From a cloned checkout:

```bash
docker build -t owntinfoil .
docker run --rm -p 8080:8080 --env-file .env \
  -v "$PWD/NPSdir:/nps" \
  -v "$PWD/TORRENTdir:/torrents" \
  owntinfoil
```

Create `.env` from `.env.example` first. This starts the HTTP shop and bot synchronization; the Compose setup additionally provides Transmission to process downloaded torrent files.

### Generate configuration documentation

Descriptions and examples live in `Field(...)` declarations in [app/config.py](app/config.py). After changing settings, regenerate both the reference and `.env.example`:

```bash
uv run --locked pydantic-settings-export
```

The exporter uses the `Settings` class defaults, so local credentials are not written into generated files. The `pydantic-settings-export` hook keeps these files current.

### Checks and Git hooks

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked ty check
uv run --locked python -m unittest discover -s tests -v
uv run --locked prek run --all-files
```

Install Git hooks with `uv run prek install`. Hooks use the official Ruff, uv, ty, and actionlint repositories plus the published `pydantic-settings-export` hook. Their revisions are pinned in `.pre-commit-config.yaml`. Tests use temporary files and local HTTP fixtures; they do not contact the bot or download real torrents.

Update dependencies with `uv lock --upgrade` followed by `uv sync --locked`.

## License

[MIT](LICENSE)
