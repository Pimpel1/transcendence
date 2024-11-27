FROM python:3.12-alpine3.19

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /tmp/requirements.txt
COPY requirements.dev.txt /tmp/requirements.dev.txt
EXPOSE 8004

ARG DEV=false

RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    rm -rf /tmp && \
    addgroup \
        --system \
        translation-group && \
    adduser \
        --system \
        --ingroup translation-group \
        --no-create-home \
        translation-user

ENV PATH="/py/bin:$PATH"

COPY . /translation_service
COPY ./ssl/ /etc/ssl/
RUN rm -rf /translation_service/ssl && \
    chown -R translation-user:translation-group \
        /translation_service /etc/ssl

USER translation-user
WORKDIR /translation_service

CMD ["sh", "-c", "uvicorn translation_service.asgi:application \
        --host 0.0.0.0 \
        --port 8004 \
        --ssl-keyfile /etc/ssl/translation-service.key \
        --ssl-certfile /etc/ssl/translation-service.crt"]