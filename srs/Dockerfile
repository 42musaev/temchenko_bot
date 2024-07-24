FROM python:3.12-alpine
RUN apk add --no-cache gcc musl-dev libffi-dev tzdata && \
    pip install --no-cache-dir poetry && \
    apk del gcc musl-dev libffi-dev
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi
COPY . .
ENV TZ=UTC
CMD ["python", "app.py"]
