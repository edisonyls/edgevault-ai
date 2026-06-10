# EdgeVault Backend

FastAPI backend managed with `uv`.

## Setup

```bash
uv sync
```

## Run

```bash
uv run fastapi dev app/main.py
```

The API is available at `http://127.0.0.1:8000`.

## Test

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check .
uv run ruff format .
```
