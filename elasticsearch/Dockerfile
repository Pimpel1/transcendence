FROM docker.elastic.co/elasticsearch/elasticsearch:7.10.2

RUN mkdir -p /usr/share/elasticsearch/config /etc/ssl/certs

COPY ./elasticsearch.yml /usr/share/elasticsearch/config/elasticsearch.yml
COPY ./ssl/elasticsearch.p12 /usr/share/elasticsearch/config/elasticsearch.p12
COPY setup-elasticsearch.sh /usr/share/elasticsearch/setup-elasticsearch.sh

RUN chown elasticsearch:elasticsearch /usr/share/elasticsearch/config/elasticsearch.p12
RUN chmod 600 /usr/share/elasticsearch/config/elasticsearch.p12
RUN chmod +x /usr/share/elasticsearch/setup-elasticsearch.sh

WORKDIR /usr/share/elasticsearch
USER elasticsearch
EXPOSE 9200

CMD ["/bin/sh", "-c", "/usr/share/elasticsearch/setup-elasticsearch.sh & /usr/local/bin/docker-entrypoint.sh eswrapper"]
