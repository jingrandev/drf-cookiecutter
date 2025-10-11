# Define an alias for the specific python version used in this file.
FROM docker.io/python:{{ cookiecutter.python_version }}-slim-bookworm AS python

# Python build stage
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=local

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  {%- if cookiecutter.database_engine == 'postgres' %}
  # psycopg build deps
  libpq-dev
  {%- elif cookiecutter.database_engine == 'mysql' %}
  # mysqlclient build deps
  default-libmysqlclient-dev
  {%- endif %}

# Requirements are installed here to ensure they will be cached.
COPY ./requirements/ ./requirements/

# Install Python deps
RUN pip install --no-cache-dir -r requirements/base.txt
RUN pip install --no-cache-dir -r requirements/develop.txt

# Python 'run' stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  {%- if cookiecutter.database_engine == 'postgres' %}
  # psycopg runtime deps
  libpq-dev \
  {%- elif cookiecutter.database_engine == 'mysql' %}
  # mysqlclient runtime library
  libmariadb3 \
  {%- endif %}
  # Translations dependencies
  gettext \
  # wait-for-it
  wait-for-it \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/local/lib/python{{ cookiecutter.python_version }}/site-packages /usr/local/lib/python{{ cookiecutter.python_version }}/site-packages

# Copy application code to WORKDIR
COPY . ${APP_HOME}

# Copy entrypoint
COPY ./compose/local/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

ENTRYPOINT ["/entrypoint"]
