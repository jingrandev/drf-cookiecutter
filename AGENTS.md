# AGENTS.md — drf-cookiecutter

## Project Overview

This is a **Cookiecutter template** that generates production-ready Django REST Framework projects. It is NOT a Django project itself — it is a Jinja2-based scaffolding template.

Running `cookiecutter .` or `cookiecutter https://github.com/...` renders the `{{cookiecutter.project_slug}}/` directory into a real Django project with all boilerplate in place.

## Template Structure

```
drf-cookiecutter/
├── cookiecutter.json              # User prompts & default values
├── hooks/
│   ├── pre_gen_project.py         # Validation before generation
│   └── post_gen_project.py        # Post-generation cleanup
├── {{cookiecutter.project_slug}}/ # Template source (Jinja2 variables everywhere)
│   ├── config/                    # Django project settings
│   ├── core/                      # Shared framework code
│   │   ├── admin/                 # Admin framework layer (security gate middleware; future base ModelAdmins, dashboard)
│   │   ├── auth/                  # Custom User model + JWT auth
│   │   ├── db/                    # BaseModel, SoftDelete, managers, querysets
│   │   ├── restframework/         # DRF extensions (renderer, error handler, pagination, viewsets)
│   │   └── tests/                 # Tests for core modules
│   ├── apps/api/                  # Example business app
│   ├── libs/
│   │   ├── logging/               # Loguru setup
│   │   └── http_client/           # HTTP client wrapper
│   ├── compose/                   # Docker files (local + production)
│   ├── docker-compose.local.yml
│   ├── Makefile
│   └── pyproject.toml
├── tests/                         # Tests for the cookiecutter template itself
├── pyproject.toml                 # Template development dependencies
└── tox.ini
```

## cookiecutter.json Options

| Variable              | Type                           | Description                                     |
| --------------------- | ------------------------------ | ----------------------------------------------- |
| `project_name`        | string                         | Human-readable project name                     |
| `project_slug`        | auto-derived                   | Directory/files slug (from project_name)        |
| `description`         | string                         | Project description                             |
| `author_name`         | string                         | Author name                                     |
| `email`               | string                         | Contact email                                   |
| `version`             | string                         | Initial version (default 0.1.0)                 |
| `username_type`       | choice: `username`, `email`    | Changes User model and auth flow                |
| `open_source_license` | choice                         | MIT, BSD, GPLv3, Apache 2.0, or Not open source |
| `python_version`      | choice: `3.12`, `3.13`, `3.14` | Target Python version                           |
| `database_engine`     | choice: `postgres`, `mysql`    | Database engine (affects deps, Docker, config)  |

Jinja2 conditionals in the template use these variables: `{% if cookiecutter.username_type == "email" %}`, `{%- if cookiecutter.database_engine == 'postgres' %}`, etc.

## Development Commands

### Template development (this repo)

```bash
# Install dependencies
uv sync

# Run all template tests via tox (generates project, validates structure)
tox

# Run specific test environment
tox -e py313
tox -e ruff

# Lint & format the template code
ruff check .
ruff format .

# Lint Jinja2 templates
djlint {{cookiecutter.project_slug}} --lint
djlint {{cookiecutter.project_slug}} --check
```

### Generated project commands (after running cookiecutter)

```bash
make init          # Create venv + install deps via uv
make run           # Run dev server
make test          # Run pytest
make lint          # Ruff check
make typecheck     # mypy
make fix           # Ruff check --fix + format
make migrations    # makemigrations
make migrate       # migrate
```

## Generated Project Architecture

### Layered design

- **config/** — Django settings split into `base.py`, `local.py`, `test.py`. Environment via `django-environ` (`DATABASE_URL`, `DJANGO_SECRET_KEY`, etc.).
- **core/** — Shared framework code, not business logic. Never modify for a single app's needs.
  - **core/auth/** — Custom User model (`AUTH_USER_MODEL = "authentication.User"`), JWT authentication (Cookie + Bearer), Djoser integration. Full layering: `models/`, `serializers/`, `services/`, `views/`, `endpoints/`, `utils/`.
  - **core/db/** — `BaseModel` (created_at, updated_at), `SoftDeleteBaseModel` (+ is_deleted, deleted_at, id_copy), `ActiveManager`/`AllObjectsManager`, `SoftDeleteQuerySet`.
  - **core/restframework/** — Unified response envelope, error handler, pagination, base viewsets, filters, OpenAPI hooks, middleware.
- **apps/** — Business applications. Each app under `apps/`. Example: `apps/api/`.
- **libs/** — Reusable utilities: `logging/` (Loguru), `http_client/`.

### Key patterns in generated project

1. **Unified response envelope** — All API responses are wrapped in `{code, data, message}` via `StandardResponseRenderer`. Success: `code: 0`. Errors: specific codes.

2. **Unified error handling** — Registry-based `ExceptionHandler` in `core/restframework/error_handler.py`. Each exception type maps to a `HandlerRule` with error code, message, and optional hooks. Extend by calling `ExceptionHandler.register()`.

3. **Soft delete** — `SoftDeleteMixin` provides `delete()` (soft), `hard_delete()`, `restore()`. Default manager `objects` returns only active records; `all_objects` returns everything.

4. **Dual JWT auth** — `CookieJWTAuthentication` reads JWT from cookies; standard `JWTAuthentication` reads from Authorization header. Both active by default.

5. **API versioning** — URL prefix `/api/v1/` via `drf_spectacular` schema prefix.

6. **Admin security gate** — `core/admin/middleware.py` (`AdminGateMiddleware`). When `ADMIN_SECURITY_CODE` env var is set, all `/admin/` paths return 404 until the visitor opens `/admin/<code>/`, which sets a session flag and redirects to the admin. Unset = gate disabled. Unlock is handled inside the middleware (not a URL route) to avoid colliding with single-segment admin URLs like `/admin/login/`. The module is intentionally a plain package (no `apps.py`, not in `INSTALLED_APPS`) so its label can't clash with `django.contrib.admin`; it is the admin framework layer — also hosts `navigation.py` (Unfold sidebar callback) and `callbacks.py` (environment badge), and future extensions (base ModelAdmins, dashboard callbacks, filters, actions) belong here too.

## Testing

### Template tests (tests/)

- `test_cookiecutter_generation.py` — Generates project from template, validates file structure, checks Jinja2 rendering.
- `test_hooks.py` — Tests pre/post generation hooks.
- `test_bare.sh` — Shell-based smoke test.

Run with: `tox` or `pytest tests/`

### Generated project tests

- pytest + pytest-django, `--no-migrations` mode, `--reuse-db`
- Settings module: `config.settings.test`
- Coverage source: `core`, `apps`

## Conventions

- **No comments** in code unless explicitly requested.
- **Ruff** for linting and formatting. Line length: 119 in template, 88 in generated project.
- **Import sorting**: `isort` with `force-single-line` in generated project.
- **Jinja2 templates**: formatted with `djlint` (profile: `jinja`).
- **Type hints**: mypy with `django-stubs` and `djangorestframework-stubs`.
- **Pre-commit**: Both this repo and generated projects use pre-commit hooks.
- **Python version**: Template requires >=3.12. Generated project targets user-selected version (3.12–3.14).
- **Django version**: Generated project targets Django 6.0.

## Adding New Template Features

1. Add new variables to `cookiecutter.json` if user choice is needed.
2. Use Jinja2 conditionals `{% if %}` / `{%- endif %}` in affected files.
3. Update `hooks/post_gen_project.py` for any file creation/removal based on choices.
4. Add tests in `tests/` to validate generation with new options.
5. Run `tox` to verify all matrix combinations pass.
6. Run `djlint {{cookiecutter.project_slug}} --lint` to check template formatting.

## Important Notes

- Files under `{{cookiecutter.project_slug}}/` are Jinja2 templates, NOT valid Python. They contain `{{ }}` and `{% %}` syntax that only resolves after cookiecutter runs.
- The `tox.ini` configures test environments for multiple Python versions. Always run the full matrix before merging.
- The template uses `uv` as the package manager for generated projects (not pip/poetry).
- Docker Compose configuration is generated based on `database_engine` choice (postgres or mysql).
