FROM python:3.12-alpine3.19

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
EXPOSE 8000

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache \
        postgresql-client \
        postgresql-dev \
        curl && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        gcc python3-dev musl-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    addgroup \
        --system \
        django-group && \
    adduser \
        --system \
        --ingroup django-group \
        --no-create-home \
        django-user

ENV PATH="/py/bin:$PATH"

COPY . /game_service
COPY ./ssl/ /etc/ssl/
RUN rm -rf /game_service/ssl && \
    chown -R django-user:django-group \
        /game_service /etc/ssl

USER django-user
WORKDIR /game_service

CMD ["sh", "-c", "python manage.py wait && \
        uvicorn game_service.asgi:application \
            --host 0.0.0.0 \
            --port 8000 \
            --ssl-keyfile /etc/ssl/game-service.key \
            --ssl-certfile /etc/ssl/game-service.crt"]
