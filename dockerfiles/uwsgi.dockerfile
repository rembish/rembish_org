FROM python:latest AS builder

ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

COPY poetry.lock pyproject.toml ./
RUN pip install poetry && mkdir /build && poetry export $(test "$FLASK_ENV" == development && echo "--dev") > /build/requirements.txt
WORKDIR /build
COPY dockerfiles .

FROM python:latest

EXPOSE 5000

WORKDIR /app
COPY --from=builder /build/requirements.txt ./
COPY rembish_org rembish_org/
RUN pip install -r requirements.txt \
    && rm -rf rembish_org/static && rm requirements.txt
COPY dockerfiles/uwsgi.dockerfile /Dockerfile

CMD ["uwsgi", "--module", "rembish_org:create_app()"]
