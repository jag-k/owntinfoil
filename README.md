# OwnTinfoil in Docker

Port on Python of the OwnTinfoil project.

## How to ...

### How to use

1. Copy the [docker-compose.yml](docker-compose.yml) file in your own directory
2. Edit the file and change the `BOT_URL` and `BOT_KEY` (if you have it) variables.
3. Run `docker-compose up -d`
4. Enjoy!

### How to update

1. Run `docker-compose pull`
2. Run `docker-compose up -d`
3. Enjoy!

### How to stop

1. Run `docker-compose down`
2. Enjoy!

### How to remove

1. Run `docker-compose down --rmi all`
2. Enjoy!

## Development

### Requirements

* [Python 3.11](https://www.python.org/)
* [Poetry 1.4.1](https://python-poetry.org/)
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
