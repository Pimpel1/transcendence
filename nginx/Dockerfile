FROM nginx:1.27.0-alpine

RUN addgroup \
        --system \
        nginx-group && \
    adduser \
        --system \
        --ingroup nginx-group \
        --no-create-home \
        nginx-user && \
    mkdir -p /var/cache/nginx && \
    mkdir -p /var/run/ && \
    mkdir -p /static/ && \
    mkdir -p /etc/nginx/ssl/ && \
	mkdir -p /temp/ && \
    rm /etc/nginx/conf.d/default.conf

COPY ./nginx/nginx.conf /etc/nginx/
COPY ./nginx/ssl.conf /etc/nginx/conf.d/
COPY ./nginx/cors.conf /etc/nginx/conf.d/
COPY ./nginx/logging.conf /etc/nginx/conf.d/
COPY ./nginx/server.conf /etc/nginx/conf.d/
COPY ./nginx/ssl/ /etc/nginx/ssl/
COPY ./nginx/ip_config.sh /temp/
COPY ./web_app/ /static/
RUN chown -R nginx-user:nginx-group /var/cache/nginx && \
    chown -R nginx-user:nginx-group /var/run/ && \
    chown -R nginx-user:nginx-group /var/log/ && \
    chown -R nginx-user:nginx-group /static/ && \
    chown -R nginx-user:nginx-group /etc/nginx/ && \
	chmod +x /temp/ip_config.sh

USER nginx-user

CMD /temp/ip_config.sh && nginx -g "daemon off;"
