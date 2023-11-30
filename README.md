# OwnTinfoil in Docker

[![GitHub Container Registry Build](https://img.shields.io/github/actions/workflow/status/jag-k/owntinfoil/deploy.yml?logo=github&label=Container%20Registry
)](https://github.com/users/jag-k/packages/container/package/owntinfoil)


Port on Python of the OwnTinfoil project.

More info you can find in [project's Wiki](https://github.com/jag-k/owntinfoil/wiki)

## Usage

### Requirements:

* [Docker](https://www.docker.com/)
* [Docker Compose](https://docs.docker.com/compose/)

### Install:

1. Copy the [docker-compose.yml](docker-compose.yml) file in your own directory
2. Edit the file and change the `BOT_URL` and `BOT_KEY` (if you have it) variables.
3. Run `docker-compose up -d`
4. Enjoy!

## How to ...

You can read the [Wiki page](https://github.com/jag-k/owntinfoil/wiki/How-to) for more information.

Also, you can read the [FAQ page](https://github.com/jag-k/owntinfoil/wiki/FAQ) for more information.

## Development

### Requirements:

* [Python 3.11](https://www.python.org/)
* [Poetry 1.7.1](https://python-poetry.org/)
* [Docker](https://www.docker.com/) (optional)

### How to install

1. Clone the repository
2. Run `poetry install`
3. Enjoy!

### How to run

1. Add the `BOT_URL` and `BOT_KEY` (if you have it) variables in the `.env` file.
2. Run `poetry run python -m app`
3. Enjoy!

## License

[MIT](LICENSE)
