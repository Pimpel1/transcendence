FROM python:3.12-alpine3.19

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
EXPOSE 8002

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache \
        postgresql-client \
        postgresql-dev && \
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
        matchmaker-group && \
    adduser \
        --system \
        --ingroup matchmaker-group \
        --no-create-home \
        matchmaker-user

ENV PATH="/py/bin:$PATH"

COPY . /matchmaker_service
COPY ./ssl/ /etc/ssl/
RUN rm -rf /matchmaker_service/ssl && \
    chown -R matchmaker-user:matchmaker-group \
        /matchmaker_service /etc/ssl

USER matchmaker-user
WORKDIR /matchmaker_service

CMD ["sh", "-c", "python manage.py wait_for_user_management && \
        python manage.py migrate && \
        uvicorn matchmaker_service.asgi:application \
            --host 0.0.0.0 \
            --port 8002 \
            --ssl-keyfile /etc/ssl/matchmaker-service.key \
            --ssl-certfile /etc/ssl/matchmaker-service.crt"]
