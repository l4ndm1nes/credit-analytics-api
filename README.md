# Credit Analytics API

HTTP/JSON service for analyzing a lending portfolio: users, credits, payments, and monthly
issuance/collection plans. Built on FastAPI + SQLAlchemy 2.x (async) + MySQL 8, packaged with Docker.

## Architecture

The project follows Clean (Onion) Architecture. Dependencies point strictly inward:
`api → application → domain`, `infrastructure → application/domain`.

```
app/
├── domain/               entities, enums, domain exceptions (pure Python)
├── application/          use cases, repository interfaces (Protocol), DTOs
├── infrastructure/       SQLAlchemy models, repositories, UoW, Excel parser, seed, auth
└── api/                  FastAPI routers, Pydantic schemas, DI, exception handlers
```

Key principles:

- Use cases receive a `UnitOfWork` and depend only on repository interfaces — they know nothing
  about ORM.
- The FastAPI layer is thin: request/response validation and a use-case call.
- Fully async/await, including the MySQL connection through `asyncmy`.
- Money is stored as `NUMERIC(18,2)` and always represented as `Decimal`.
- Domain exceptions are translated into HTTP responses with a unified error envelope.

## Stack

| Component | Version |
|---|---|
| Python | 3.11 |
| FastAPI | 0.115 |
| SQLAlchemy | 2.0 (async) |
| Alembic | 1.14 |
| MySQL | 8.0 (`asyncmy` driver) |
| Pydantic | 2.10 |
| Auth | JWT (HS256) or `X-API-Key` (controlled by `AUTH_MODE`) |

## Authentication

Two modes, switched via the `AUTH_MODE` environment variable:

- `jwt` (default) — obtain a token via `POST /api/v1/auth/token` (login + password),
  then pass `Authorization: Bearer <token>` on every request.
- `api_key` — each request must include the `X-API-Key: <api_key>` header.

On startup a service user is created automatically
(`BOOTSTRAP_ADMIN_LOGIN` / `BOOTSTRAP_ADMIN_PASSWORD`).

## Running with Docker

```bash
cp .env.example .env
docker compose up --build
```

Services:

- `db` — MySQL 8 with a healthcheck;
- `migrate` — runs `alembic upgrade head` and exits;
- `api` — FastAPI + Uvicorn, starts only after `migrate` completes successfully.

Once everything is up, Swagger UI is available at http://localhost:8000/docs.

Initial data can be loaded from CSV files (inside a running container):

```bash
docker compose exec api python -m scripts.seed_from_csv
```

or automatically on API startup by setting `SEED_ON_STARTUP=true` in `.env`.

## Running locally without Docker

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

export DATABASE_URL="mysql+asyncmy://credit_app:credit_app@localhost:3306/credit_analytics"
alembic upgrade head
python -m scripts.seed_from_csv
uvicorn app.main:app --reload
```

## Testing

Unit and integration tests run with a single command (they use a file-backed SQLite via aiosqlite):

```bash
pytest
pytest --cov=app --cov-report=term-missing
```

Layout:

- `tests/unit/` — use cases (via `FakeUnitOfWork`), security/JWT, Excel parser.
- `tests/integration/` — FastAPI + `httpx.AsyncClient` + `aiosqlite`: full auth flow and
  every business endpoint.

## Endpoints

Base path: `/api/v1`.

| Method | Path | Description |
|---|---|---|
| POST | `/auth/token` | Issue a JWT (`{login, password}`) |
| GET | `/user_credits/{user_id}` | Credits of a given user |
| POST | `/plans_insert` | Upload an Excel file with plans |
| GET | `/plans_performance?check_date=YYYY-MM-DD` | Plan performance as of a date |
| GET | `/year_performance?year=YYYY` | Year-long monthly summary |

### Error format

```json
{
  "error": {
    "code": "invalid_plans_file",
    "message": "plans file contains errors",
    "details": [
      {"location": "row 2, period", "message": "period must be the first day of a month"}
    ]
  }
}
```

## Request examples

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H 'Content-Type: application/json' \
  -d '{"login":"admin","password":"admin"}' | jq -r .access_token)

curl -s http://localhost:8000/api/v1/user_credits/1 \
  -H "Authorization: Bearer $TOKEN" | jq

curl -s -X POST http://localhost:8000/api/v1/plans_insert \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@plans.xlsx" | jq

curl -s "http://localhost:8000/api/v1/plans_performance?check_date=2024-06-01" \
  -H "Authorization: Bearer $TOKEN" | jq

curl -s "http://localhost:8000/api/v1/year_performance?year=2024" \
  -H "Authorization: Bearer $TOKEN" | jq
```

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async database URL (`mysql+asyncmy://...`) |
| `AUTH_MODE` | `jwt` or `api_key` |
| `JWT_SECRET_KEY` | Secret used for HS256 |
| `JWT_ACCESS_TOKEN_TTL_MINUTES` | Token TTL |
| `API_KEY` | Key used when `AUTH_MODE=api_key` |
| `BOOTSTRAP_ADMIN_LOGIN` / `BOOTSTRAP_ADMIN_PASSWORD` | Service user for JWT auth |
| `SEED_ON_STARTUP` | Auto-load CSVs from `SEED_DATA_DIR` at startup |
| `SEED_DATA_DIR` | Directory with CSV source files |

The full list lives in `.env.example`.

## Development

```bash
ruff check .
ruff format .
mypy app
pytest
```
