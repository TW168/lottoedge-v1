# GitHub Copilot Engineering Rules — Python

You are a senior Python software engineer responsible for producing production-quality code for this project.
All generated code must follow professional software engineering standards including modular design,
documentation, and maintainable architecture.

---

## 1. Package Management

- **Always use `uv`** to add, remove, or update packages. Never use `pip install` directly.

```bash
uv add "fastapi[standard]" asyncpg python-dotenv
uv remove <package>
uv sync
```

---

## 2. Project Stack

| Layer       | Library                  |
|-------------|--------------------------|
| Web API     | FastAPI (`fastapi[standard]`) |
| Database    | asyncpg (async PostgreSQL)   |
| Config      | python-dotenv, configparser for INI-style `.env` |
| Server      | uvicorn (via `fastapi[standard]`) |
| Runtime     | Python ≥ 3.12, managed with `uv` |

### Environment configuration
The `.env` file uses an INI-style `[postgresql]` section with lowercase keys:

```ini
[postgresql]
host=your-host
port=5432
database=your_db
user=your_user
password=your_password
sslmode=require
```

Config loaders must support both an INI `[postgresql]` section **and** standard
`POSTGRES_*` / `DATABASE_URL` env vars, with env vars taking precedence.

---

## 3. Mandatory Modular Architecture

Every project must follow this layout. **No large single-file implementations.**

```
project/
    app/
        api/
            routes/          # HTTP endpoints only — no business logic
        services/            # Business logic
        models/              # ORM / database models
        schemas/             # Pydantic validation & serialisation schemas
        repositories/        # All database operations (SQL / asyncpg calls)
        core/                # Config, lifespan, connection pool setup
        utils/               # Reusable helpers
    tests/
        unit/
        integration/
    docs/
        architecture.md
        requirements.md
        api_specification.md
        database_schema.md
        development_guidelines.md
    main.py                  # FastAPI app factory + lifespan only
    pyproject.toml
    .env
```

**Layer responsibilities enforced strictly:**

- `api/routes` → receive request, call service, return response
- `services` → orchestrate business logic, call repositories
- `repositories` → execute SQL / asyncpg queries, return domain objects
- `models` → database table definitions
- `schemas` → Pydantic models for request/response validation
- `core` → `settings.py`, `database.py` (pool creation / teardown)
- `utils` → stateless helper functions

---

## 4. Python Coding Standards

- **PEP 8** formatting enforced
- **Black**-compatible, **88 character** line length
- **Full type hints** on all function signatures and class attributes
- **PEP 257 docstrings** on every module, class, and function

### Naming conventions

| Target     | Convention   |
|------------|--------------|
| variables  | `snake_case` |
| functions  | `snake_case` |
| classes    | `PascalCase` |
| constants  | `UPPER_CASE` |

---

## 5. Mandatory Docstrings — Google Style

Every function **must** have a docstring in Google style.

```python
def get_database_version(conn: asyncpg.Connection) -> str:
    """Fetch the PostgreSQL server version string.

    Args:
        conn: An active asyncpg database connection.

    Returns:
        The full version string from `SELECT version()`.

    Raises:
        asyncpg.PostgresError: If the query fails.
    """
    ...
```

---

## 6. Code Comments — Explain *Why*, Not *What*

Comments must explain intent, trade-offs, or non-obvious design decisions.

```python
# Normalize text so search-index comparisons are case-insensitive
normalized = text.lower()
```

---

## 7. API Endpoint Documentation Standard

Each endpoint must be documented before implementation:

```
Endpoint Purpose: <short description>
Method: GET | POST | PUT | PATCH | DELETE
Route: /path
Request Body / Params: <fields + types>
Example Request: { ... }
Example Response: { ... }
```

In code, populate `summary`, `description`, `tags`, `response_model`, and `status_code`
on every `@app.get / @app.post` decorator.

---

## 8. Error Handling

- Use `HTTPException` for all client-facing errors with appropriate status codes.
- Wrap all database calls in `try/except` and re-raise as `HTTPException(500)` with a
  safe (non-sensitive) detail message.
- Never expose raw exception messages or stack traces to API consumers.

---

## 9. SOLID Principles

- **Single Responsibility**: one module, one reason to change.
- **Open/Closed**: extend via new modules; do not modify stable interfaces.
- **Liskov Substitution**: repository abstractions must be substitutable.
- **Interface Segregation**: keep service interfaces narrow.
- **Dependency Inversion**: inject dependencies; do not instantiate inside functions.

---

## 10. Testing Requirements

Tests must be included when generating new features.

```
tests/
    unit/        # Pure logic, no I/O, mocked dependencies
    integration/ # Real database or HTTP calls (use a test database)
```

Use `pytest` with `pytest-asyncio` for async tests.

---

## 11. Required Documentation (Always Keep Updated)

Whenever a feature changes, update the corresponding docs file:

| File                          | Contents                              |
|-------------------------------|---------------------------------------|
| `docs/architecture.md`        | System architecture, data flow, dependencies |
| `docs/requirements.md`        | Functional & non-functional requirements |
| `docs/api_specification.md`   | All endpoint contracts                |
| `docs/database_schema.md`     | Table definitions, relationships      |
| `docs/development_guidelines.md` | Setup, coding conventions, runbook |

### requirements.md format

```markdown
## System Overview
## Functional Requirements
## Non-Functional Requirements
## Constraints
## Future Enhancements
```

---

## 12. Maintainability Rules

When modifying code:

- Update docs and requirements in the same change.
- Keep functions small and focused (≤ 30 lines as a guideline).
- Avoid tight coupling between layers — route handlers must not import from repositories directly.
- Do not duplicate logic — extract shared code to `utils/` or a base service.
