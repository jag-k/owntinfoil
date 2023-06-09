FROM python:3.11-slim

WORKDIR /app

ENV NPS_DIR=/nps
ENV TORRENT_DIR=/torrents
ENV PYTHONPATH=/app
ENV POETRY_VERSION=1.4.1

RUN pip install "poetry==$POETRY_VERSION"
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --without dev

COPY . /app

CMD ["python", "app/main.py"]
