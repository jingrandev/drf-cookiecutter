.PHONY: help
help: ## Print this help menu
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: require
require: ## Check that prerequisites are installed.
	@if ! command -v uv > /dev/null; then \
		printf "\033[1m\033[31mERROR\033[0m: uv not installed.\n" >&2 ; \
		printf "Please install with 'pipx install uv'\n" >&2 ; \
		exit 1; \
		fi

.PHONY: init
init: require .setup_complete ## Set up the local development environment

.setup_complete: ## Internal helper to run the setup
	uv venv --python {{ cookiecutter.python_version }} --seed && .venv/bin/activate
	uv sync
	touch .setup_complete

.PHONY: teardown
teardown: ## Remove local development environment
	rm -rf .venv
	rm -f .setup_complete

.PHONY: fix
fix: ## Fix all files in-place using ruff
	ruff check --fix .
	ruff format .

.PHONY: check
check: ## Run pre-commit hooks on all files
	@command -v pre-commit > /dev/null 2>&1 || (printf "\033[1m\033[31mERROR\033[0m: pre-commit not installed\n" >&2; exit 1)
	pre-commit run --all-files

.PHONY: lint
lint: ## Run linters on all files
	ruff check .

.PHONY: typecheck
typecheck: ## Run static type checks using mypy
	mypy .

.PHONY: test
test: ## Run unit tests
	pytest

.PHONY: cov
cov: ## Run tests with coverage
	pytest --cov=. --cov-report=term

.PHONY: lines
lines: ## Count lines of project code
	which cloc > /dev/null 2>&1 && cloc . --exclude-dir=.venv || find . -name "*.py" | xargs cat | wc -l

.PHONY: cleanup
cleanup: ## Clean up project files and caches
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf silk
	find . -name '*.py[cod]' -delete
	find . -name '__pycache__' -delete
	find . -name '*.c' -delete
	find . -name '*.h' -delete
	find . -name '*.so' -delete

.PHONY: run
run: ## Run the Django development server (make run 0.0.0.0:8000)
	python manage.py runserver $(filter-out $@,$(MAKECMDGOALS))

.PHONY: migrations
migrations: ## Create database migrations (make migrations app_name)
	python manage.py makemigrations $(filter-out $@,$(MAKECMDGOALS))

.PHONY: migrate
migrate: ## Apply database migrations (make migrate app_name)
	python manage.py migrate $(filter-out $@,$(MAKECMDGOALS))

%:
	@:
