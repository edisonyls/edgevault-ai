# EdgeVault AI

EdgeVault AI is a self-hosted document vault for receipts, invoices, bills, and other
financial paperwork. It combines OCR, structured financial extraction, semantic search,
and a constrained natural-language assistant so private documents can stay on hardware
you control.

The project is designed around an edge-first deployment model, including Raspberry Pi
hardware, PostgreSQL with pgvector, Tesseract OCR, and optional OpenAI-compatible LLM
tiers for assistant intent parsing.

## Features

- Upload and store PDF/image documents.
- Extract embedded PDF text or fall back to Tesseract OCR for scanned files.
- Convert OCR text into structured financial records: vendor, type, dates, amount,
  currency, category, and payment status.
- Preserve manual corrections and avoid overwriting human-edited records.
- Search documents with keyword, semantic, or hybrid search.
- Ask constrained natural-language questions backed by deterministic database queries.
- Manage vendor classification rules.
- View dashboard summaries and spending trends in the frontend.
- Separate owner and demo workspaces through cookie-based session auth.

## Tech Stack

Backend:

- Python 3.14
- FastAPI
- PostgreSQL, asyncpg, and pgvector
- Tesseract OCR, pytesseract, and PyMuPDF
- fastembed using `BAAI/bge-small-en-v1.5`
- uv for dependency management

Frontend:

- Next.js 16 app router
- React 19 and TypeScript
- HeroUI v3
- Tailwind CSS v4
- Chart.js

## Repository Layout

```text
edgevault-ai/
|-- backend/                 FastAPI API service
|   |-- app/
|   |   |-- api/routes/       HTTP route handlers
|   |   |-- core/             settings, auth, database, events
|   |   |-- repositories/     SQL data-access layer
|   |   |-- schemas/          Pydantic request/response models
|   |   `-- services/         OCR, extraction, search, assistant, embeddings
|   |-- db/migrations/        SQL migrations
|   |-- docs/                 extraction and RAG evaluation notes
|   |-- scripts/              migration, embedding, eval, and probing scripts
|   `-- tests/                backend tests
|-- frontend/                Next.js frontend
|   `-- src/
|       |-- app/              app-router pages
|       |-- components/       shared layout and UI components
|       |-- config/           navigation and app config
|       `-- features/         feature-scoped API, hooks, components, types
|-- docs/                    architecture and deployment notes
`-- .github/workflows/       independent frontend/backend deploy workflows
```

## Prerequisites

- PostgreSQL with the pgvector extension available.
- Tesseract OCR installed on the host.
- uv for the backend.
- Node.js and npm for the frontend.

Install Tesseract:

```bash
# macOS
brew install tesseract

# Debian / Ubuntu / Raspberry Pi OS
sudo apt install tesseract-ocr
```

## Backend Setup

From the repository root:

```bash
cd backend
uv sync
cp .env.example .env
```

Edit `backend/.env` and set the required values:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/edgevault
AUTH_OWNER_PASSWORD=change-me
AUTH_DEMO_PASSWORD=change-me
AUTH_SESSION_SECRET=change-me
ASSISTANT_LLM_MODEL=qwen2.5-coder:1.5b
```

Run migrations and start the API:

```bash
uv run python scripts/migrate.py
uv run fastapi dev app/main.py
```

The API runs at:

```text
http://127.0.0.1:8000
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Note: `CREATE EXTENSION vector` may require a PostgreSQL superuser. If your app database
role cannot create extensions, enable pgvector once manually before running migrations.

## Frontend Setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:3000
```

Set the backend URL with `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Configuration

Backend settings are loaded from `backend/.env`. See `backend/.env.example` and
`backend/app/core/config.py` for the full list.

Common settings:

```env
NODE_ENV=development
DATABASE_URL=postgresql://user:password@localhost:5432/edgevault
UPLOAD_STORAGE_DIR=var/uploads

AUTH_OWNER_PASSWORD=
AUTH_DEMO_PASSWORD=
AUTH_SESSION_SECRET=

OCR_ENGINE=tesseract
OCR_PDF_TEXT_THRESHOLD=20
OCR_PDF_RENDER_DPI=200

EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

ASSISTANT_LLM_BASE_URL=http://localhost:8000/v1
ASSISTANT_LLM_MODEL=qwen2.5-coder:1.5b
ASSISTANT_LLM_TIMEOUT=30
ASSISTANT_LLM_KEEP_WARM=true

ASSISTANT_FALLBACK_ENABLED=false
ASSISTANT_FALLBACK_BASE_URL=https://api.deepseek.com
ASSISTANT_FALLBACK_MODEL=DeepSeek-V4-Flash
DEEPSEEK_API_KEY=
```

The assistant uses deterministic rules first. LLM tiers are used only for translating
questions into supported structured intents; database queries still produce the returned
numbers.

## API Overview

All backend routes are mounted under `/api`.

| Method   | Path                                 | Description                               |
| -------- | ------------------------------------ | ----------------------------------------- |
| `GET`    | `/api/health`                        | Health check                              |
| `POST`   | `/api/auth/login`                    | Log in to a workspace                     |
| `GET`    | `/api/auth/session`                  | Read the current session                  |
| `POST`   | `/api/auth/logout`                   | Log out                                   |
| `POST`   | `/api/uploads`                       | Upload a document                         |
| `GET`    | `/api/uploads`                       | List uploads                              |
| `GET`    | `/api/uploads/events`                | Stream upload/extraction events           |
| `GET`    | `/api/uploads/{id}`                  | Get upload metadata and extraction status |
| `GET`    | `/api/uploads/{id}/extractions`      | Get extraction history                    |
| `GET`    | `/api/uploads/{id}/financial-record` | Get the structured financial record       |
| `PATCH`  | `/api/uploads/{id}`                  | Update upload metadata                    |
| `DELETE` | `/api/uploads/{id}`                  | Delete an upload                          |
| `GET`    | `/api/financial-records`             | List financial records                    |
| `PATCH`  | `/api/financial-records/{id}`        | Correct a financial record                |
| `GET`    | `/api/search`                        | Search documents                          |
| `GET`    | `/api/documents`                     | Search/list documents                     |
| `POST`   | `/api/assistant/query`               | Ask a supported natural-language question |
| `GET`    | `/api/vendor-rules`                  | List vendor rules                         |
| `POST`   | `/api/vendor-rules`                  | Create a vendor rule                      |
| `PATCH`  | `/api/vendor-rules/{id}`             | Update a vendor rule                      |
| `DELETE` | `/api/vendor-rules/{id}`             | Delete a vendor rule                      |

Example assistant request:

```bash
curl -X POST http://127.0.0.1:8000/api/assistant/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What did I spend the most on this month?"}'
```

## Development Commands

Backend:

```bash
cd backend
uv run ruff check .
uv run ruff format .
uv run pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Deployment

Deployment is handled by two independent GitHub Actions workflows:

- `.github/workflows/deploy-frontend.yml`
- `.github/workflows/deploy-backend.yml`

The workflows are intended for separate self-hosted runners or VMs. See
`docs/deployment.md` for required secrets, runner requirements, and optional assistant
LLM deployment settings.

## Additional Documentation

- `docs/deployment.md` - deployment workflows and VM requirements.
- `backend/docs/eval_baseline.md` - financial extraction evaluation notes.
- `backend/docs/rag_extractor.md` - RAG extractor experiment notes.

## Project Status

This is an open-source personal and learning project. It is functional, but it should not
be treated as a hardened commercial document-management system without further security,
privacy, and reliability review.

## License

No formal license is currently included in this repository.
