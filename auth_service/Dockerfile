FROM python:3.12-alpine3.19

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
EXPOSE 8001

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache \
        postgresql-client \
        postgresql-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        gcc python3-dev musl-dev libffi-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    addgroup \
        --system \
        auth-group && \
    adduser \
        --system \
        --ingroup auth-group \
        --no-create-home \
        auth-user

ENV PATH="/py/bin:$PATH"

COPY . /auth_service
COPY ./ssl/ /etc/ssl/
RUN rm -rf /auth_service/ssl && \
    chown -R auth-user:auth-group \
        /auth_service /etc/ssl

USER auth-user
WORKDIR /auth_service

CMD ["sh", "-c", "uvicorn auth_service.asgi:application \
        --host 0.0.0.0 \
        --port 8001 \
        --ssl-keyfile /etc/ssl/auth-service.key \
        --ssl-certfile /etc/ssl/auth-service.crt"]
