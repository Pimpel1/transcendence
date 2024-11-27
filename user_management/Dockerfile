FROM python:3.12-alpine3.19

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

EXPOSE 8003

ARG DEV=false

RUN python -m venv /py && \
    apk add -u zlib-dev jpeg-dev gcc musl-dev && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache \
        postgresql-client \
        postgresql-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        gcc python3-dev musl-dev \
        jpeg-dev zlib-dev libjpeg && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    addgroup \
        --system \
        user-management-group && \
    adduser \
        --system \
        --ingroup user-management-group \
        --no-create-home \
        user-management-user

ENV PATH="/py/bin:$PATH"

COPY . /user_management
COPY ./ssl/ /etc/ssl/
RUN rm -rf /user_management/ssl && \
    mkdir -p /user_management/media/avatars && \
    chown -R user-management-user:user-management-group \
        /user_management /etc/ssl /user_management/media/avatars

USER user-management-user
WORKDIR /user_management

CMD ./manage.py wait_for_auth_service && \
    ./manage.py migrate && \
    uvicorn user_management.asgi:application \
        --host 0.0.0.0 \
        --port 8003 \
        --ssl-keyfile /etc/ssl/user-management.key \
        --ssl-certfile /etc/ssl/user-management.crt
