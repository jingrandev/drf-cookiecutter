# Define an alias for the specific python version used in this file.
FROM docker.io/python:{{ cookiecutter.python_version }}-slim-bookworm AS python

# Python build stage
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=local
ARG PIP_PACKAGES=""

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  {%- if cookiecutter.database_engine == 'postgres' %}
  # psycopg build deps
  libpq-dev
  {%- elif cookiecutter.database_engine == 'mysql' %}
  # mysqlclient build deps
  pkg-config \
  default-libmysqlclient-dev \
  python3-dev
  {%- endif %}

# Requirements are installed here to ensure they will be cached.
COPY ./requirements/ ./requirements/

# Install Python deps
RUN pip install --no-cache-dir -r requirements/base.txt
RUN pip install --no-cache-dir -r requirements/develop.txt

RUN if [ -n "$PIP_PACKAGES" ]; then pip install --no-cache-dir ${PIP_PACKAGES}; fi

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
  less \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# copy python dependency wheels and binaries from python-build-stage
COPY --from=python-build-stage /usr/local/lib/python{{ cookiecutter.python_version }}/site-packages /usr/local/lib/python{{ cookiecutter.python_version }}/site-packages
COPY --from=python-build-stage /usr/local/bin /usr/local/bin

RUN printf '%s\n' \
  '#!/usr/bin/env bash' \
  'exec python manage.py shell "$@"' \
  > /usr/local/bin/pmsh \
  && printf '%s\n' \
  '#!/usr/bin/env bash' \
  'exec python manage.py runscript "$@"' \
  > /usr/local/bin/pms \
  && chmod +x /usr/local/bin/pmsh /usr/local/bin/pms \
  && printf '%s\n' \
  "alias pmsh='python manage.py shell'" \
  "alias pms='python manage.py runscript'" \
  > /etc/profile.d/django-aliases.sh \
  && cat /etc/profile.d/django-aliases.sh >> /root/.bashrc

# Copy application code to WORKDIR
COPY . ${APP_HOME}

# Copy entrypoint
COPY ./compose/local/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start
{%- if cookiecutter.use_celery == "yes" %}

COPY ./compose/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r$//g' /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./compose/local/django/celery/flower/start /start-flower
RUN sed -i 's/\r$//g' /start-flower
RUN chmod +x /start-flower
{%- endif %}

ENTRYPOINT ["/entrypoint"]
