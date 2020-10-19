FROM python:latest

EXPOSE 5000
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

WORKDIR /app
COPY poetry.lock pyproject.toml Dockerfile ./
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install $(test "$FLASK_ENV" == production && echo "--no-dev") --no-interaction --no-ansi \
    && pip uninstall --yes poetry
COPY rembish_org rembish_org/

CMD ["uwsgi", "--module", "rembish_org:create_app()"]
