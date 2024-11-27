FROM docker.elastic.co/kibana/kibana:7.10.2

USER root
COPY ./kibana.yml /usr/share/kibana/config/kibana.yml
COPY ./ssl/kibana.crt /usr/share/kibana/config/kibana.crt
COPY ./ssl/kibana.key /usr/share/kibana/config/kibana.key
COPY ./ssl/elasticsearch.crt /usr/share/kibana/config/elasticsearch.crt
COPY dashboards.ndjson /usr/share/kibana/dashboards/
COPY setup-kibana.sh /usr/share/kibana/setup-kibana.sh

RUN chmod 644 /usr/share/kibana/config/*.crt /usr/share/kibana/config/*.key
RUN chmod 644 /usr/share/kibana/config/kibana.yml
RUN chmod +x /usr/share/kibana/setup-kibana.sh

USER kibana
WORKDIR /usr/share/kibana
EXPOSE 5601

CMD ["sh", "-c", "/usr/share/kibana/setup-kibana.sh & kibana-docker"]
